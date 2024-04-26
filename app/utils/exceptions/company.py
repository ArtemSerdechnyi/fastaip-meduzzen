class CompanyNotFoundException(Exception):
    def __init__(self, message="Company not found.", **kwargs):
        self.message = f"{message} Kwargs: {kwargs}" if kwargs else message
        super().__init__(self.message)
