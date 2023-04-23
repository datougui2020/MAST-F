import os
import logging
import shutil

from uuid import UUID

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status, views
from rest_framework.authentication import (
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication
)

from django.shortcuts import get_object_or_404
from django.db.models import QuerySet
from django.contrib import messages

from celery.result import AsyncResult

from mastf.MASTF.serializers import ScanSerializer, CeleryResultSerializer
from mastf.MASTF.models import (
    Scan,
    Project,
    ScanTask,
    Scanner,
)
from mastf.MASTF.forms import ScanForm
from mastf.MASTF.rest.permissions import ReadOnly, CanEditScan
from mastf.MASTF.scanners.plugin import ScannerPlugin
from mastf.MASTF.utils.upload import handle_scan_file_upload
from mastf.MASTF.workers import tasks

from .base import (
    APIViewBase,
    ListAPIViewBase,
    CreationAPIViewBase,
    GetObjectMixin
)

logger = logging.getLogger(__name__)

__all__ = [
    'ScanView', 'ScanCreationView', 'ScanListView',
    'ScannerView', 'ScanTaskView'
]

class ScanView(APIViewBase):
    permission_classes = [IsAuthenticated & (CanEditScan | ReadOnly)]
    model = Scan
    serializer_class = ScanSerializer
    lookup_field = 'scan_uuid'

    def on_delete(self, request: Request, obj: Scan) -> None:
        path = obj.project.dir(obj.file.internal_name, create=False)
        try:
            os.remove(obj.file.file_path)
            shutil.rmtree(str(path))
        except OSError as err:
            messages.error(request, str(err), err.__class__.__name__)


class ScanCreationView(CreationAPIViewBase):
    form_class = ScanForm
    model = Scan

    permission_classes = [IsAuthenticated]

    def set_defaults(self, request, data: dict) -> None:
        data['initiator'] = request.user
        data['risk_level'] = 'None'
        data['status'] = 'Scheduled'
        if not data['start_date']:
            # The date would be set automatically
            data.pop('start_date')

        # remove the delivered scanners
        plugins = ScannerPlugin.all()
        selected = []
        for i in range(len(plugins)):
            # Remove each scanner so that it won't be used
            # to create the Scan object
            name = self.request.POST.get(f"selected_scanners_{i}", None).lower()
            if not name or name not in plugins:
                break

            # Even if the scanner is present, we have to add it
            # to the list of scanners to start
            selected.append(name)

        if len(selected) == 0:
            logger.warning('No scanner selected - aborting scan generation')
            raise ValueError('At least one scanner has to be selected')

        # As the QueryDict is mutable, we can store the selected
        # parameters before we're starting each scanner
        setattr(self.request.POST, '_mutable', True)
        self.request.POST['selected_scanners'] = selected

        # the file has to be downloaded before any action shoule be executed
        file_url = data.pop('file_url', None)
        if not file_url:
            uploaded_file = handle_scan_file_upload(self.request.FILES['file'], data['project'])
            if not uploaded_file:
                raise ValueError('Could not save uploaded file')

            self.request.POST['File'] = uploaded_file
        else:
            raise NotImplementedError('URL not implemented!')

    def on_create(self, request: Request, instance: Scan) -> None:
        tasks.schedule_scan(
            instance, request.POST['File'],
            request.POST['selected_scanners']
        )


class ScanListView(ListAPIViewBase):
    serializer_class = ScanSerializer
    queryset = Scan.objects.all()

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        # TODO: maybe control via GET parameter whether public scans
        # should be returned as well
        return queryset.filter(initiator=self.request.user)


class ScannerView(views.APIView):

    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        TokenAuthentication
    ]

    permission_classes = [IsAuthenticated & CanEditScan]

    def get(self, request: Request, scan_uuid: UUID, name: str,
            extension: str) -> Response:
        """Generates a result JSON for each scanner extension

        :param request: the HttpRequest
        :type request: Request
        :param scan_id: the scan's ID
        :type scan_id: UUID
        :param name: the scanner's name
        :type name: str
        :param extension: the extension to query
        :type extension: str
        :return: the results as JSON string
        :rtype: Response
        """
        # TODO: maybe add pagination
        scan = get_object_or_404(Scan.objects.all(), scan_uuid=scan_uuid)
        plugins = Scanner.names(scan.project)

        if name not in plugins:
            return Response(status=status.HTTP_404_NOT_FOUND)

        plugin: ScannerPlugin = ScannerPlugin.all()[name]
        if extension not in plugin.extensions:
            return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

        results = plugin.results(extension, scan)
        return Response(results)


class ScanTaskView(GetObjectMixin, views.APIView):
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        TokenAuthentication
    ]

    permission_classes = [IsAuthenticated & CanEditScan]

    model = ScanTask
    lookup_field = 'task_uuid'

    def get(self, request: Request, task_uuid: UUID) -> Response:
        task: ScanTask = self.get_object()
        if not task.celery_id:
            data = CeleryResultSerializer.empty()
        else:
            result = AsyncResult(task.celery_id)
            data = CeleryResultSerializer(result).data

        return Response(data)
