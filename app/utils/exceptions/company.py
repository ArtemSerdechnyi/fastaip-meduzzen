class CompanyNotFoundException(Exception):
    def __init__(self, message="Company not found.", **kwargs):
        self.message = f"{message} Kwargs: {kwargs}" if kwargs else message
        super().__init__(self.message)


class CompanyMemberNotFoundException(Exception):
    def __init__(self, message="Company member not found.", **kwargs):
        self.message = f"{message} Kwargs: {kwargs}" if kwargs else message
        super().__init__(self.message)


class CompanyRequestNotFoundException(Exception):
    def __init__(self, message="Company invite not found.", **kwargs):
        self.message = f"{message} Kwargs: {kwargs}" if kwargs else message
        super().__init__(self.message)
