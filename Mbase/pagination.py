from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ProductPagination(PageNumberPagination):
    page_size = 8  # Default number of items per page
    page_size_query_param = "page_size"  # Allow the client to set page size
    max_page_size = 100  # Limit the maximum number of items per page

    # customizing paginated response
    def get_paginated_response(self, data):
        return Response(
            {
                "pagination": {
                    "current_page": self.page.number,
                    "total_pages": self.page.paginator.num_pages,
                    "total_items": self.page.paginator.count,
                    "page_size": self.get_page_size(self.request),
                },
                "results": data,
            }
        )
