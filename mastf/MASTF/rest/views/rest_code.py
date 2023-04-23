from os.path import commonprefix
from django.shortcuts import get_object_or_404

from rest_framework import permissions, authentication, views
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from mastf.MASTF import settings
from mastf.MASTF.rest.permissions import CanEditProject, CanEditScan
from mastf.MASTF.models import Finding, Vulnerability, Project, File, Scan
from mastf.MASTF.serializers import SnippetSerializer
from mastf.MASTF.utils import filetree


from .base import GetObjectMixin

__all__ = [
    'FindingCodeView', 'VulnerabilityCodeView', 'FiletreeView', 'FileCodeView'
]

class CodeView(views.APIView):

    authentication_classes = [
        authentication.BasicAuthentication,
        authentication.SessionAuthentication,
        authentication.TokenAuthentication
    ]

    permission_classes = [
        permissions.IsAuthenticated & CanEditProject
    ]

    model = None

    def get(self, request: Request, finding_id: str) -> Response:
        finding = get_object_or_404(self.model.objects.all(), finding_id=finding_id)

        snippet = finding.snippet
        if not snippet:
            return Response({'detail': 'No Code assigned to this template'}, status.HTTP_204_NO_CONTENT)

        src_file = snippet.sys_path
        language = snippet.language
        if not src_file or not language:
            return Response({'detail': 'Invalid file pointer'}, status.HTTP_204_NO_CONTENT)

        # validate whether the requesting user has the necessary
        # permissions to view the file
        project = finding.scan.project
        self.check_object_permissions(request, project)

        # Either provide the whole file or send a code
        # snippet with all relevant lines
        path = settings.PROJECTS_ROOT / str(project.project_uuid) / str(finding.scan.file.md5) / "src"
        if not path.exists():
            return Response({'detail': "Project source file directory does not exist"},
                            status.HTTP_500_INTERNAL_SERVER_ERROR)

        path = path / language / src_file
        if not path.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        with path.open(encoding='utf-8') as fp:
            code = fp.read()

        serializer = SnippetSerializer(snippet)
        data = {
            'code': code,
            'snippet': serializer.data
        }
        return Response(data)

class FindingCodeView(CodeView):
    model = Finding

class VulnerabilityCodeView(CodeView):
    model = Vulnerability

class FiletreeView(GetObjectMixin, views.APIView):
    authentication_classes = [
        authentication.BasicAuthentication,
        authentication.SessionAuthentication,
        authentication.TokenAuthentication
    ]

    permission_classes = [
        permissions.IsAuthenticated & CanEditScan
    ]

    model = Scan
    lookup_field = 'scan_uuid'

    def get(self, request, *args, **kwargs):
        scan: Scan = self.get_object()
        target = scan.project.dir(scan.file.internal_name)

        # The root node's name must be changed as it would display
        # the md5 hash value
        tree = filetree.apply_rules(target, scan.file.internal_name)
        tree['type'] = 'projectstructure'
        tree['text'] = scan.file.file_name
        return Response(tree)

class FileCodeView(GetObjectMixin, views.APIView):
    authentication_classes = [
        authentication.BasicAuthentication,
        authentication.SessionAuthentication,
        authentication.TokenAuthentication
    ]

    permission_classes = [
        permissions.IsAuthenticated
    ]

    model = File
    lookup_field = 'internal_name'

    def get(self, request: Request, *args, **kwargs) -> Response:
        scan_file = self.get_object()
        scan = Scan.objects.get(file=scan_file)

        permission = CanEditScan()
        if not permission.has_object_permission(request, self, scan):
            self.permission_denied(
                request,
                message=getattr(permission, 'message', None),
                code=getattr(permission, 'code', None)
            )

        path = request.query_params.get("file", None)
        safe_dir = f"{scan_file.internal_name}/"
        if not path or not commonprefix((safe_dir, path)):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        target = scan.project.directory / path
        if not target.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(open(str(target), 'rb'))

