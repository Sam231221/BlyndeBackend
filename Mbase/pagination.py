from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ProductPagination(PageNumberPagination):
    page_size = 8  # Default number of items per page
    page_size_query_param = "products_limit"  # Allow the client to set page size
    max_page_size = 100  # Limit the maximum number of items per page

    def get_paginated_response(self, data):
        return Response(
            {
                "pagination": {
                    "current_page": self.page.number,
                    "total_pages": self.page.paginator.num_pages,
                    "total_items": self.page.paginator.count,
                    "page_size": self.get_page_size(
                        getattr(self, "request", None)
                    ),  # Safe request handling
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "results": data,
            }
        )


class OrderPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = "limit"  # Allow client to override page size
    max_page_size = 100  # Set a maximum page size

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "results": data,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            }
        )
