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
import collections
import datetime
import yaml


def flatten_dict(dictionary, parent_key='', sep='_'):
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, collections.MutableMapping):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def convert_size(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T']:
        if abs(num) < 1024.0:
            return ["%3.2f" % num, "%s%s" % (unit, suffix)]
        num /= 1024.0
    return ["%.2f" % num, "%s%s" % ('Yi', suffix)]


def get_api_url(context_map):
    if os.getenv("ICGCGET_API_URL"):
        api_url = os.getenv("ICGCGET_API_URL")
    else:
        api_url = context_map["portal_url"] + 'api/v1/'
    return api_url


def normalize_keys(obj):
    if isinstance(obj, dict):
        return obj
    else:
        return {k.replace('.', '_'): normalize_keys(v) for k, v in obj.items()}


def config_parse(filename):
    config = {}
    try:
        config_text = open(filename, 'r')
    except IOError:

        return config
    try:
        config_temp = yaml.safe_load(config_text)
        config_download = flatten_dict(normalize_keys(config_temp))
        config = {'download': config_download, 'report': config_download, 'version': config_download,
                  'check': config_download, 'logfile': config_temp['logfile']}
    except yaml.YAMLError:

        return {}

    return config


def donor_addition(donor_list, donor, data_type):
    if data_type not in donor_list:
        donor_list[data_type] = []
    if donor not in donor_list['total']:
        donor_list['total'].append(donor)
    if donor not in donor_list[data_type]:
        donor_list[data_type].append(donor)
    return donor_list


def increment_types(typename, count_dict, size):
    if typename not in count_dict:
        count_dict[typename] = 0
    count_dict["total"] += size
    count_dict[typename] += size

    return count_dict


def build_table(table, repo, sizes, counts, donors, downloads):
    for data_type in sizes:
        file_size = convert_size(sizes[data_type])
        if data_type == 'total':
            name = repo
        else:
            name = repo + ": " + data_type
        if data_type not in downloads:
            downloads[data_type] = 0
        table.append([name, file_size[0], file_size[1], counts[data_type], len(donors[data_type]),
                      downloads[data_type]])
    return table


def calculate_size(manifest_json):
    size = 0
    object_ids = {}
    for repo_info in manifest_json["entries"]:
        repo = repo_info["repo"]
        object_ids[repo] = {}
        for file_info in repo_info["files"]:
            object_ids[repo][file_info['id']] = {'uuid': file_info["repoFileId"], 'state': "Not started",
                                                 'filename': 'None', 'index_filename': 'None',
                                                 'fileUrl': 'None', 'size': file_info['size']}
            size += file_info["size"]
    session_info = {'pid': os.getpid(), 'start_time': datetime.datetime.now(), 'object_ids': object_ids}
    return size, session_info
