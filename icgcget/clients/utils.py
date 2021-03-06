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
import collections
import os
import click


def build_table(table, repo, sizes, counts, donors, downloads, output):
    """
    Function to create a nested list 'table" for the report function.
    :param table:
    :param repo:
    :param sizes:
    :param counts:
    :param donors:
    :param downloads:
    :param output:
    :return:
    """
    for data_type in sizes:
        file_size = convert_size(sizes[data_type])
        if data_type == 'total':
            name = repo
        else:
            name = repo + ': ' + data_type
        if output:
            if data_type not in downloads:
                downloads[data_type] = 0
            table.append([name, file_size[0], file_size[1], counts[data_type], len(donors[data_type]),
                          downloads[data_type]])
        else:
            table.append([name, file_size[0], file_size[1], counts[data_type], len(donors[data_type])])
    return table


def calculate_size(manifest_json, download_session):
    """
    Function that calculates the total size of download based on manifest json return.  Also initializes the file
    data object for a download
    :param manifest_json:
    :param download_session:
    :return:
    """
    size = 0
    file_data = {}
    for repo_info in manifest_json['entries']:
        repo = repo_info['repo']
        file_data[repo] = {}
        for file_info in repo_info['files']:
            file_data[repo][file_info['id']] = {'uuid': file_info['repoFileId'], 'state': 'Not started',
                                                'fileName': 'None', 'index_filename': 'None',
                                                'fileUrl': 'None', 'size': file_info['size']}
            size += file_info['size']
    download_session['file_data'] = file_data
    return size, download_session


def convert_size(num, suffix='B'):
    """
    Function that converts size in bits to a human readable format
    :param num:
    :param suffix:
    :return:
    """
    for unit in ['', 'K', 'M', 'G', 'T']:
        if abs(num) < 1024.0:
            return ['%3.2f' % num, '%s%s' % (unit, suffix)]
        num /= 1024.0
    return ['%.2f' % num, '%s%s' % ('Yi', suffix)]


def donor_addition(donor_list, donor, data_type):
    """
    Adds donors and data types to lists of donors compiled during report formatting
    :param donor_list:
    :param donor:
    :param data_type:
    :return:
    """
    if data_type not in donor_list:
        donor_list[data_type] = []
    if donor not in donor_list['total']:
        donor_list['total'].append(donor)
    if donor not in donor_list[data_type]:
        donor_list[data_type].append(donor)
    return donor_list


def flatten_dict(dictionary, parent_key='', sep='_'):
    """
    Function that breaks down nested dictionaries into a single level dictionary.  Calls itself recursively
    :param dictionary:
    :param parent_key:
    :param sep: separator for new keys that are combinations of the nested path.
    :return:
    """
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + sep + key if parent_key else key
        new_value = None if value == '' else value
        if isinstance(new_value, collections.MutableMapping):  # if value is a dict, flatten it.
            items.extend(flatten_dict(new_value, new_key, sep=sep).items())
        else:
            items.append((new_key, new_value))
    return dict(items)


def flatten_file_data(file_data):
    """
    Function to get all file ids from a file_data object
    :param file_data:
    :return:
    """
    file_ids = []
    for repo in file_data:
        file_ids.extend(file_data[repo].keys())
    return file_ids


def increment_types(typename, count_dict, size):
    """
    Function used during report table construction to tally the number of files for each data type
    :param typename:
    :param count_dict:
    :param size:
    :return:
    """
    if typename not in count_dict:
        count_dict[typename] = 0
    count_dict["total"] += size
    count_dict[typename] += size

    return count_dict


def normalize_keys(obj):
    """
    Recursive function that filters keys from python conventions to yaml conventions
    :param obj:
    :return:
    """
    if isinstance(obj, dict):
        return obj
    else:
        return {k.replace('.', '_'): normalize_keys(v) for k, v in obj.items()}


def search_recursive(filename, output):
    """
    Function to recursively search through a directory and all of it's children for a file name.
    :param filename:
    :param output:
    :return:
    """
    if not output:
        return False
    for root, dirs, files in os.walk(output, topdown=False):
        for name in files:
            if name == filename:
                return True
        for directory in dirs:
            if directory == filename:
                return True
    return False


def client_style(output):
    formatted = '  | {}'.format(output)
    return click.style(formatted, fg='green')

