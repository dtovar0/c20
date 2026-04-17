class HomeService:
    @staticmethod
    def get_welcome_message():
        try:
            # Business logic could go here
            return "Professional Flask Architecture"
        except Exception as e:
            raise e
