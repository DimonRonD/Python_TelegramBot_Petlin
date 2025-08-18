from telegram.ext import Application as PTBApplication, ApplicationBuilder
from Settings.config import AppSettings # type: ignore
import logging
from src.python_telegrambot_petlin.app.handlers import HANDLERS # type: ignore





class Application(PTBApplication):
    def __init__(self, app_settings: AppSettings, **kwargs):
        super().__init__(**kwargs)
        self._settings = app_settings
        self._register_handlers()

    def run(self) -> None:
        self.run_polling()

    def _register_handlers(self):
        for handler in HANDLERS:
            self.add_handler(handler)

# Создать класс Calendar
class Calendar:
    def __init__(self):
        self.events = {}

    # Создать метод create_event
    def create_event(self, event_name, event_date, event_time, event_details):
        event_id = len(self.events) + 1
        event = {
            "id": event_id,
            "name": event_name,
            "date": event_date,
            "time": event_time,
            "details": event_details
        }
        self.events[event_id] = event
        return event_id


def configure_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

def create_app(app_settings: AppSettings) -> Application:
    application = ApplicationBuilder().application_class(Application, kwargs={'app_settings': app_settings}).token(app_settings.TELEGRAM_API_KEY.get_secret_value()).build()
    return application  #type: ignore[return-value]

if __name__ == "__main__":
    configure_logging()
    settings = AppSettings()
    app = create_app(settings)
    app.run()




