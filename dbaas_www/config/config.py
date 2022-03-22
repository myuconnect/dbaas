"""
Config.py used by gunicorn wsgi server process
"""
import multiprocessing

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    ## get traceback info
    import threading, sys, traceback
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId,""),
            threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename,
                lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

raw_env=[
    "PYTHONPATH=/opt/ansible/app/source:/opt/ansible/app/www/dbaas",
    "REGION=NAM",
    "OPCO=MARSH",
    "DC_LOCATION=Dallas",
    "DOMAIN=CORP",
    "GIT_PYTHON_REFRESH=quiet",
    "LDAP_SERVER=usdfw1.ldap.corp.mmco.int:389",
    "SMTP_SERVER=nasa1smtp.mmc.com",
    "PYTHONIOENCODING=utf8"
]
#workers=multiprocessing.cpu_count() * 2 + 1
user="ansible"
group="ansible"
workers=3
bind="0.0.0.0:5000"
threads=4
keepalive=10
backlog=2048
worker_class="gevent"
worker_connections=1000
max_requests_jitter = 1000
timout=30
limit_request_line = 1024
limit_request_fields = 100
pidfile="/opt/ansible/app/www/dbaas/www.dbaas.pid"
errorlog='/opt/ansible/app/www/dbaas/log/www_dbaas_wsgi_error.log'
loglevel='debug'
accesslog='/opt/ansible/app/www/dbaas/log/www_dbaas_wsgi_access.log'
access_log_format='%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
logfile="/opt/ansible/app/www/dbaas/log/www_dbaas_wsgi.log"
logger_class = "gunicorn.glogging.Logger"
proc_name="mmc.www.dbaas.wsgi"
chdir="/opt/ansible/app/www/dbaas"
pythonpath="/opt/ansible/app/source:/opt/ansible/app/www/dbaas"
daemon=False
