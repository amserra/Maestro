# Start virtual environment
alias venv=". venv/bin/activate";

# Starts development server
alias runserver="python manage.py runserver";

# Starts tailwind css development server
alias runtailwind="python manage.py tailwind start";

# Makes migrations
function makeMigrationsFunc {
    python manage.py makemigrations "$1";
}
alias makemigrations=makeMigrationsFunc;

# Applies migrations
alias migrate="python manage.py migrate";

# Creates a new app
function startAppFunc {
    python manage.py startapp "$1";
}
alias startApp=startAppFunc;

# Opens python shell
alias shell="python manage.py shell";

# Dump a database data into JSON
function dumpDataFunc {
    python manage.py dumpdata "$1" --ident 2 > "$1".json;
}
alias dumpdata=dumpDataFunc;

# Other aliases
alias startRabbitmq="brew services start rabbitmq";
alias stopRabbitmq="brew services stop rabbitmq";
alias startCelery="celery -A rivercureproject worker -l INFO";

# Docs: start sphinx live server
alias sphinxLive="sphinx-reload docs/";
alias sphinxBuild="cd docs/ && make build";

# Test all keeping db
alias test="python manage.py test --keepdb";

# Test and generate coverage report
alias testCoverage="coverage run --source='.' manage.py test --keepdb && coverage report";

# Generate test coverage HTML
alias coverageHtml="coverage html";