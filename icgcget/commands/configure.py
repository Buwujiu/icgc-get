#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 The Ontario Institute for Cancer Research. All rights reserved.
#
# This program and the accompanying materials are made available under the terms of the GNU Public License v3.0.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import os
import click
import yaml

from icgcget.commands.utils import config_parse
from icgcget.params import ReposParam, LogfileParam


class ConfigureDispatcher(object):

    def __init__(self, config_destination, default):
        """
        Init function parses any previous config.yaml files found in the configuration directory
        :param config_destination:
        :param default:
        """
        self.old_config = {}
        self.default_dir = os.path.split(default)[0]
        self.gnos_repos = ["pcawg-heidelberg", "pcawg-london", "pcawg-chicago-icgc", "pcawg-tokyo", "pcawg-seoul",
                           "pcawg-barcelona", "pcawg-chicago-tcga", "pcawg-cghub"]
        if os.path.isfile(config_destination):
            old_config = config_parse(config_destination, default, empty_ok=True)
            if old_config:
                self.old_config = old_config['report']

    def configure(self, config_destination):
        """
        Series of prompts that gathers info needed for the config.yaml file.
        :param config_destination:
        :return:
        """
        config_directory = os.path.split(config_destination)
        if not os.path.isdir(config_directory[0]):
            raise click.BadOptionUsage("Unable to write to directory {}".format(config_directory[0]))
        print "You will receive a series of prompts for all relevant configuration values and access parameters "
        print "Existing configuration values are listed in square brackets.  To keep these values, press Enter."
        print "To input multiple values for a prompt, separate each value with a space.\n"

        message = "Enter a directory on your machine for downloaded files to be saved to."
        output = self.prompt('output', 'output', message, input_type=click.Path(exists=True, writable=True,
                                                                                file_okay=False, resolve_path=True))
        message = "Enter a location for the process logs to be stored.  Must be in an existing directory.  Optional."
        logfile = self.prompt('logfile', 'logfile', message, input_type=LogfileParam())
        message = "Enter which repositories you want to download from.\n" + \
                  "Valid repositories are: aws-virginia gnos collaboratory ega gdc pdc"
        repos = self.prompt('repos', 'repos', message, input_type=ReposParam())
        message = "Enter true or false if you wish to use a docker container to download and run all download clients"
        docker = self.prompt('docker', 'docker', message, input_type=click.BOOL)
        conf_yaml = {'output': output, 'logfile': logfile, 'repos': repos, 'docker': docker}
        if "aws-virginia" in repos or "collaboratory" in repos:
            message = "Enter the path to your local ICGC storage client installation"
            icgc_path = self.prompt('ICGC path', 'icgc_path', message,
                                    input_type=click.Path(exists=True, dir_okay=False, resolve_path=True), skip=docker)
            icgc_access = self.prompt('ICGC token', 'icgc_token', "Enter a valid ICGC access token")
            if icgc_path:
                conf_yaml['icgc'] = {'token': icgc_access, 'path': icgc_path}
            else:
                conf_yaml["icgc"] = {'token': icgc_access}
        gnos_specified = [repo for repo in self.gnos_repos if repo in repos]
        if gnos_specified:
            gnos_path = self.prompt('gnos path', 'gnos_path', "Enter the path to your local genetorrent binaries",
                                    input_type=click.Path(exists=True, dir_okay=False, resolve_path=True), skip=docker)
            gnos_keys = {}
            for repo in gnos_specified:
                repo_code = repo.split('-')[-1]
                key = self.prompt(repo.upper() + ' key', 'gnos_key_' + repo_code, "Enter your " + repo.upper() + " key")
                gnos_keys[repo_code] = key
            if gnos_path:
                conf_yaml['gnos'] = {'key': gnos_keys, 'path': gnos_path}
            else:
                conf_yaml["gnos"] = {'key': gnos_keys}
        if "ega" in repos:
            ega_path = self.prompt('EGA path', 'ega_path', "Enter the path to your local EGA download client jar file",
                                   input_type=click.Path(exists=True, dir_okay=False, resolve_path=True), skip=docker)
            ega_username = self.prompt('EGA username', 'ega_username', "Enter your EGA username")
            ega_password = self.prompt('EGA password', 'ega_password', "Enter your EGA password")
            if ega_path:
                conf_yaml['ega'] = {'username': ega_username, 'password': ega_password, 'path': ega_path}
            else:
                conf_yaml["ega"] = {'username': ega_username, 'password': ega_password}

        if "gdc" in repos:
            message = "Enter the path to your local GDC download client installation"
            gdc_path = self.prompt('GDC path', 'gdc_path', message,
                                   input_type=click.Path(exists=True, dir_okay=False, resolve_path=True), skip=docker)

            gdc_access = self.prompt('GDC token', 'gdc_token', "Enter a valid GDC access token")
            if gdc_path:
                conf_yaml['gdc'] = {'token': gdc_access, 'path': gdc_path}
            else:
                conf_yaml["gdc"] = {'token': gdc_access}
        if "pdc" in repos:
            message = "Enter the path to your local AWS-cli installation to access the PDC repository"
            pdc_path = self.prompt('AWS path', 'pdc_path', message,
                                   input_type=click.Path(exists=True, dir_okay=False, resolve_path=True), skip=docker)
            pdc_key = self.prompt('PDC key', 'pdc_key', "Enter your PDC s3 key")
            pdc_secret_key = self.prompt('PDC secret key', 'pdc_secret', "Enter your PDC s3 secret key", hide=True)
            if pdc_path:
                conf_yaml['pdc'] = {'key': pdc_key, 'secret': pdc_secret_key, 'path': pdc_path}
            else:
                conf_yaml['pdc'] = {'key': pdc_key, 'secret': pdc_secret_key}
        config_file = open(config_destination, 'w')
        yaml.safe_dump(conf_yaml, config_file, encoding=None, default_flow_style=False)
        os.environ['ICGCGET_CONFIG'] = config_destination
        print "Configuration file saved to {}".format(config_file.name)

    def prompt(self, value_string, value_name, info, input_type=click.STRING, hide=False, skip=False):
        if value_name in self.old_config and self.old_config[value_name]:
            if value_name == 'repos':
                default = ' '.join(self.old_config[value_name])
            else:
                default = self.old_config[value_name]
        else:
            if value_name == 'logfile':
                default = self.default_dir + '/icgc_get.log'
            else:
                default = ''
        if skip:
            return default
        print '\n' + info
        value = click.prompt(value_string, default=default, hide_input=hide, type=input_type, show_default=not hide)
        if value_name == 'repos' and value == default:  # Default params do not get filtered through input_type.convert
            value = default.split(' ')
        return value
