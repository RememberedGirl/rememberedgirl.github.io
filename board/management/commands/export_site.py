from pathlib import Path
import shutil
import tempfile
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from board.views import load_data, context, home_context


class Command(BaseCommand):
    help = 'Export public HTML pages for GitHub Pages; no API calls or database access.'

    def add_arguments(self, parser):
        parser.add_argument('--output', default='_site')

    def handle(self, *args, **options):
        if not settings.PUBLIC_SNAPSHOT.is_file():
            raise CommandError('Сначала создай data/clan.json через import_snapshot.py.')
        data = load_data()
        target = Path(options['output']).resolve()
        marker = '.clan-site-export'
        if target.exists() and not (target / marker).is_file():
            raise CommandError('Каталог не принадлежит экспорту. Выбери пустой новый путь.')
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
            stage = Path(tmp) / 'site'
            stage.mkdir()
            (stage / 'index.html').write_text(render_to_string('board/home.html', home_context(data)))
            for player in data['players']:
                folder = stage / 'players' / player['slug']
                folder.mkdir(parents=True)
                (folder / 'index.html').write_text(render_to_string('board/player.html', dict(context(data, '../../'), player=player)))
            shutil.copytree(settings.BASE_DIR / 'board/static/board', stage / 'assets/board')
            (stage / '.nojekyll').touch()
            (stage / marker).touch()
            if target.exists():
                shutil.rmtree(target)
            stage.rename(target)
        self.stdout.write(self.style.SUCCESS(f'Создан сайт: {target} · Профилей: {len(data["players"])}'))
