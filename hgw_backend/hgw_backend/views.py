# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Source
from .serializers import SourceSerializer
from django.http import Http404, HttpResponse


class SourcesList(APIView):

    def get_object(self, source_id):
        try:
            return Source.objects.get(source_id=source_id)
        except Source.DoesNotExist:
            raise Http404

    def get(self, request, source_id=None, format=None):
        if source_id:
            source = self.get_object(source_id)
            serializer = SourceSerializer(source)
        else:
            sources = Source.objects.all()
            serializer = SourceSerializer(sources, many=True)
        return Response(serializer.data, content_type='application/json')


def home(request):
    return HttpResponse('<a href="/admin/">Click here to access admin page</a>')