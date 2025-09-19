from rest_framework.pagination import (
    BasePagination,
    PageNumberPagination,
    LimitOffsetPagination,
    CursorPagination,
)


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class PageNumberResultsSetPagination(PageNumberPagination):
    # page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_query_param = 'page'  # Can change to anything that you want

    def paginate_queryset(self, queryset, request, view=None):
        # Check if 'updated_at' field exists in the model
        model = queryset.model
        if hasattr(model, 'updated_at'):
            # Order by 'updated_at' if it exists
            queryset = queryset.order_by('-updated_at')
        else:
            # Otherwise, order by 'id'
            queryset = queryset.order_by('-id')

        return super().paginate_queryset(queryset,request,view)
        # Apply default ordering to the queryset
    # def get_paginated_response(self, data):
    #     return Response(
    #         {
    #             'links': {'next': self.get_next_link(), 'previous': self.get_previous_link()},
    #             'count': self.page.paginator.count,
    #             'results': data,
    #         }
    #     )

    # NOTE: If you prefer to have the count, previous link and next link in the HTTP headers
    # def get_paginated_response(self, data):
    #     response = Response(data)
    #     response['count'] = self.page.paginator.count
    #     response['next'] = self.get_next_link()
    #     response['previous'] = self.get_previous_link()
    #     return response


class LimitOffsetResultsSetPagination(LimitOffsetPagination):
    default_limit = 2
    limit_query_param = 'limit'  # Can change to anything that you want
    offset_query_param = 'offset'  # Can change to anything that you want
    max_limit = 50


class CursorResultsSetPagination(CursorPagination):
    page_size = 10
    cursor_query_param = 'cursor'  # Can change to anything that you want
    ordering = '-id'


class DynamicPagination(BasePagination):
    def paginate_queryset(self, queryset, request, view=None):
        # Determine the pagination style based on the 'pagination' query parameter
        pagination_style = request.query_params.get('pagination', 'page_number')

        if pagination_style == 'page_number':
            self.paginator = PageNumberResultsSetPagination()
        elif pagination_style == 'limit_offset':
            self.paginator = LimitOffsetPagination()
        elif pagination_style == 'cursor':
            self.paginator = CursorResultsSetPagination()
        else:
            # Default to CustomPageNumberPagination if the type is not specified or recognized
            self.paginator = PageNumberResultsSetPagination()

        return self.paginator.paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)
