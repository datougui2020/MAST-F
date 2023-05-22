import logging

from django.shortcuts import redirect
from django.db.models import QuerySet, Q
from django.contrib.auth.models import User

from celery.result import AsyncResult

from mastf.MASTF.mixins import (
    ContextMixinBase,
    UserProjectMixin,
    VulnContextMixin,
    TemplateAPIView,
)
from mastf.MASTF.models import (
    Vulnerability,
    Scan,
    ScanTask,
    Finding,
    namespace,
    Scanner,
    AbstractBaseFinding,
    Dependency,
    Project,
    Team,
)
from mastf.MASTF.serializers import CeleryAsyncResultSerializer
from mastf.MASTF.scanners.plugin import ScannerPlugin
from mastf.MASTF.rest.views import ScanCreationView
from mastf.MASTF.rest.permissions import CanEditProject
from mastf.MASTF.utils.enum import State, Severity, Visibility

__all__ = [
    "UserProjectDetailsView",
    "UserProjectScanHistoryView",
    "UserScannersView",
    "UserProjectPackagesView",
    "UserProjectConfigView",
]

logger = logging.getLogger(__name__)


class UserProjectDetailsView(UserProjectMixin, ContextMixinBase, TemplateAPIView):
    template_name = "project/project-overview.html"
    permission_classes = [CanEditProject]
    default_redirect = "Projects"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.apply_project_context(context)

        project = context["project"]
        context["active"] = "tabs-overview"
        logger.debug(
            "[%s] Preparing Project-Overview data (%s)", project.pk, project.name
        )

        vuln = Vulnerability.objects.filter(scan__project=project)
        context["risk_count"] = len(vuln)
        context["verified"] = len(vuln.filter(Q(severity=str(State.CONFIRMED))))
        context["scan"] = Scan.last_scan(project)

        tasks = ScanTask.active_tasks(project=project)
        context["is_active"] = len(tasks) > 0
        scan = context["scan"]
        if scan:
            scan.is_active = context["is_active"]
            scan.save()

        logger.debug(
            "[%s] Queried %d active tasks (is_active=%s)",
            project.pk,
            len(tasks),
            scan.is_active if scan is not None else False,
        )
        if context["is_active"] and (scan and scan.is_active):
            active_data = []
            for task in tasks:
                if task.celery_id and task.active:
                    result = AsyncResult(task.celery_id)
                    active_data.append(CeleryAsyncResultSerializer(result).data)

            context["active_data"] = active_data


        return context


class UserProjectScanHistoryView(UserProjectMixin, ContextMixinBase, TemplateAPIView):
    template_name = "project/project-scan-history.html"
    permission_classes = [CanEditProject]
    default_redirect = "Projects"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)
        self.apply_project_context(context)

        project = context["project"]
        context["active"] = "tabs-scan-history"
        context["scan_data"] = [
            self.get_scan_history(scan) for scan in Scan.objects.filter(project=project)
        ]
        return context

    def get_scan_history(self, scan: Scan) -> dict:
        data = namespace()
        vuln_data = AbstractBaseFinding.stats(Vulnerability, scan=scan)
        finding_data = AbstractBaseFinding.stats(Finding, scan=scan)

        data.scan = scan
        data.high_risks = vuln_data.high + finding_data.high
        data.medium_risks = vuln_data.medium + finding_data.medium
        data.low_risks = vuln_data.low + finding_data.low
        return data


class UserScannersView(
    UserProjectMixin, VulnContextMixin, ContextMixinBase, TemplateAPIView
):
    template_name = "project/project-scanners.html"
    permission_classes = [CanEditProject]
    default_redirect = "Projects"

    def post(self, request, *args, **kwargs):
        view = ScanCreationView.as_view()
        view(request)
        return redirect("Project-Overview", **self.kwargs)

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)
        self.apply_project_context(context)

        context["active"] = "tabs-scanners"

        project = context["project"]
        scans = Scan.objects.filter(project=project).order_by("start_date")
        scanners = ScannerPlugin.all_of(project)

        results = {}
        for name, scanner in scanners.items():
            project_scanner = Scanner.objects.filter(
                scan__project=project, name=name
            ).first()
            results[scanner.internal_name] = self.get_scan_results(scans, project_scanner)

        context["scan_results"] = results
        return context

    def get_scan_results(self, scans: QuerySet, scanner: str) -> dict:
        data = namespace()
        data.vuln_count = 0
        data.vuln_data = []
        data.start_date = None
        data.results = 0

        if len(scans) == 0:
            return data

        data.start_date = str(scans[0].start_date)
        scan_query = Q(scan=scans[0])
        for scan in scans[1:]:
            scan_query = scan_query | Q(scan=scan)

        vuln = Vulnerability.objects.filter(scan_query & Q(scanner=scanner))
        self.apply_vuln_context(
            data, AbstractBaseFinding.stats(Vulnerability, base=vuln)
        )
        data.results = len(vuln)
        return data


class UserProjectPackagesView(UserProjectMixin, ContextMixinBase, TemplateAPIView):
    template_name = "project/project-packages.html"
    permission_classes = [CanEditProject]
    default_redirect = "Projects"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.apply_project_context(context)

        context["active"] = "tabs-packages"
        context["Severity"] = [str(x) for x in Severity]
        context["dependencies"] = Dependency.objects.filter(project=context["project"])
        return context


class UserProjectConfigView(UserProjectMixin, ContextMixinBase, TemplateAPIView):
    template_name = "project/project-settings.html"
    permission_classes = [CanEditProject]
    default_redirect = "Projects"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)
        self.apply_project_context(context)

        context["active"] = "tabs-settings"
        context["risk_types"] = list(Severity)
        context["visibility_types"] = list(Visibility)
        context["available"] = list(User.objects.all())
        context["available"].remove(self.get_object(Project, "project_uuid").owner)

        context["available_teams"] = Team.get_by_owner(self.request.user)
        return context