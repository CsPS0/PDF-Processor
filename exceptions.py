class PDFProcessorError(Exception):
    pass


class OperationCancelledError(PDFProcessorError):
    pass


class DependencyMissingError(PDFProcessorError):
    def __init__(self, dependency_name, install_url=""):
        self.dependency_name = dependency_name
        self.install_url = install_url
        super().__init__(f"Required dependency not found: {dependency_name}")


class InvalidPDFError(PDFProcessorError):
    pass
