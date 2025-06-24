module.exports = {
  apps: [
    {
      name: 'autojobapply-backend',
      cwd: '/home/ubuntu/CapstoneJobAutoApply',
      script: './venv/bin/gunicorn',
      args: 'src.main:app -b 127.0.0.1:5000 -w 4',
      interpreter: './venv/bin/python3',
      env: {
        FLASK_APP: 'src/main.py',
        FLASK_ENV: 'production',
        PATH: '/home/ubuntu/CapstoneJobAutoApply/venv/bin:$PATH'
      }
    },
    {
      name: 'autojobapply-celery',
      cwd: '/home/ubuntu/CapstoneJobAutoApply',
      script: './venv/bin/celery',
      args: '-A src.services.celery_config.celery worker --loglevel=info',
      interpreter: './venv/bin/python3',
      env: {
        PATH: '/home/ubuntu/CapstoneJobAutoApply/venv/bin:$PATH'
      }
    }
  ]
}; 