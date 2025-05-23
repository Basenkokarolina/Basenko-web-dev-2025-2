class Pagination:
    def __init__(self, current_page, items_per_page, total_items, data_slice):
        self.current_page = current_page
        self.items_per_page = items_per_page
        self.total_items = total_items
        self.data_slice = data_slice

    @property
    def page_count(self):
        if self.items_per_page == 0:
            return 1
        return (self.total_items + self.items_per_page - 1) // self.items_per_page

    @property
    def has_previous(self):
        return self.current_page > 1

    @property
    def has_next(self):
        return self.current_page < self.page_count

    @property
    def previous_page(self):
        return self.current_page - 1 if self.has_previous else None

    @property
    def next_page(self):
        return self.current_page + 1 if self.has_next else None

    def display_range(self, start_edge=2, before_current=2, after_current=5, end_edge=2):
        separator_needed = 0
        for page_number in range(1, self.page_count + 1):
            is_start = page_number <= start_edge
            is_near_current = self.current_page - before_current <= page_number < self.current_page + after_current
            is_end = page_number > self.page_count - end_edge

            if is_start or is_near_current or is_end:
                if separator_needed + 1 != page_number:
                    yield None  
                yield page_number
                separator_needed = page_number
