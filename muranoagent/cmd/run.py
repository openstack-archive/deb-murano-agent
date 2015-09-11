# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys


# If ../muranoagent/__init__.py exists, add ../ to Python search path, so
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(__file__),
                                                os.pardir,
                                                os.pardir,
                                                os.pardir))
if os.path.exists(os.path.join(possible_topdir,
                               'muranoagent',
                               '__init__.py')):
    sys.path.insert(0, possible_topdir)

from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service

from muranoagent import app
from muranoagent.common import config

CONF = cfg.CONF


def main():
    try:
        config.parse_args()
        logging.setup(CONF, 'muranoagent')
        launcher = service.ServiceLauncher(CONF)
        launcher.launch_service(app.MuranoAgent())
        launcher.wait()
    except RuntimeError as e:
        sys.stderr.write("ERROR: %s\n" % e)
        sys.exit(1)


if __name__ == '__main__':
    main()
