import shutil
from context.models import SearchContext
from maestro.celery import app


@app.task(bind=True)
def delete_context_folder(self, context_id):
    context = SearchContext.objects.get(id=context_id)
    context_folder = context.context_folder
    context_folder_media = context.context_folder_media

    # Delete from DB
    if context.configuration:
        if context.configuration.advanced_configuration:
            context.configuration.advanced_configuration.delete()
        context.configuration.delete()
    context.delete()

    try:
        shutil.rmtree(context_folder)
        shutil.rmtree(context_folder_media)
        return True
    except Exception as e:
        print(e)
        return False
