from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Vendor
from .serializers import *
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from .services import WebCrawler


# Create your views here.
class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    # def create(self, request, *args, **kwargs):
    #     url = request.data.get("url")
    #     if not url:
    #         return Response({"error": "URL is required"}, status=400)
    #
    #     crawl_service = WebCrawler(max_pages=20)
    #     crawl_service.crawl(url)
    #
    #     crawl_data = crawl_service.get_data()
    #     crawl_service.reset()
    #
    #     serializer = VendorSerializer(data=crawl_data)
    #     serializer.is_valid(raise_exception=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], serializer_class=BatchCrawlInputSerializer)
    def batch_crawl(self, request):
        vendor_list = request.data
        if not isinstance(vendor_list, list):
            vendor_list = list(vendor_list)

        data = []
        crawler = WebCrawler(max_pages=20, user_agent="AbilityFamilyBOT")

        for vendor in vendor_list:
            vendor_url = vendor.get("vendor_url", None)
            if vendor_url is None:
                continue

            vendor_url = vendor_url.rstrip("/") + "/"

            vendor_programs = vendor.get("vendor_programs", [])
            for path in vendor_programs:
                crawler.programs_url_set.add(path.get("path"))

            crawler.crawl(vendor_url)
            for program in vendor_programs:
                url_path = vendor_url + program.get("path", "")

                # The path given will scan adjacent hyperlinks to gather each program information.
                # If false, any hyperlinks included are ignored and will crawl only that page.
                if program.get("scan_programs"):
                    crawler.crawl(url_path)
                else:
                    soup = crawler.get_htmlparser_soup(url_path)
                    crawler.extract_program_info(soup)

            crawl_data = crawler.get_data()
            serializer = self.get_serializer(data=crawl_data)
            if serializer.is_valid():
                serializer.save()
                data.append(serializer.data)
            else:
                print(serializer.errors)
            crawler.reset()

        return Response({"message": f"Successfully crawled {len(data)} vendors"}, status=status.HTTP_200_OK)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
