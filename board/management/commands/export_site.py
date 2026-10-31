from pathlib import Path
import shutil
import tempfile
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from board.views import load_data, context, home_context, other_clan_context


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
            for design, prefix in [('classic', ''), ('berserk', 'berserk')]:
                destination = stage / prefix
                destination.mkdir(exist_ok=True)
                templates = 'board/berserk' if design == 'berserk' else 'board'
                (destination / 'index.html').write_text(render_to_string(templates+'/home.html', home_context(data, design=design)))
                for player in data['players']:
                    folder = destination / 'players' / player['slug']
                    folder.mkdir(parents=True)
                    (folder / 'index.html').write_text(render_to_string(templates+'/player.html', dict(context(data, '../../', design), player=player)))
            if (settings.BASE_DIR / 'data/clans/2PQQ2RJ0R.json').is_file():
                clan_folder = stage / '2PQQ2RJ0R'
                clan_folder.mkdir()
                other = other_clan_context()
                (clan_folder/'index.html').write_text(render_to_string('board/other_clan.html', other))
                if other['history']:
                    for player in other['history']['players']:
                        folder = clan_folder/'players'/player['slug']
                        folder.mkdir(parents=True)
                        (folder/'index.html').write_text(render_to_string('board/masters_player.html',dict(context(other['history'],'../../','masters'),player=player)))
            shutil.copytree(settings.BASE_DIR / 'board/static/board', stage / 'assets/board')
            (stage / '.nojekyll').touch()
            (stage / marker).touch()
            if target.exists():
                shutil.rmtree(target)
            stage.rename(target)
        self.stdout.write(self.style.SUCCESS(f'Создан сайт: {target} · Дизайнов: 2 · Профилей: {len(data["players"])}'))
