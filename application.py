#!/usr/bin/env python
import os, sys, inspect

reload(sys)
sys.setdefaultencoding('utf8')

sys.path.append(os.getcwd())

from jinja2 import Environment, FileSystemLoader
from wsgiref.simple_server import make_server
from cgi import parse_qs, escape

from configuration.api import *
from configuration.settings import *

import threading
import time

import requests 

GLOBAL_LIST_OF_PARSED_COMMITS = []

class TemplateParser(object):                                                                                                                                    
    def __init__(self):
        super(TemplateParser, self).__init__()
        
        # Jinja2 -> loading&preparing template
        self.file_loader = FileSystemLoader(
            'templates'
        )
        self.env = Environment(
            loader=self.file_loader
        )
        self.template = self.env.get_template(
            MAIN_TEMPLATE_NAME
        )

    def parseBody(self, data):
        list_of_repositories = list()
        for index, item in enumerate(data):
            
            list_of_repositories.append(
                {
                    'index': (index + 1),
                    'respository_name': (
                        item["name"]
                    ).decode().encode('utf-8').strip(),
                    'created_at': (
                        item["created_at"]
                    ).decode().encode('utf-8').strip(),
                    'owner_url': (
                        item["owner"]["url"]
                    ).decode().encode('utf-8').strip(),
                    'avatar_url': (
                        item["owner"]["avatar_url"]
                    ).decode().encode('utf-8').strip(),
                    'owner_login': (
                        item["owner"]["login"]
                    ).decode().encode('utf-8').strip(),
                    'sha': (
                        item["lastest_commit"]["sha"]
                    ).decode().encode('utf-8').strip(),
                    'commit_message': (
                        item["lastest_commit"]["commit"]["message"]
                    ).decode().encode('utf-8').strip(),
                    'commit_author_name': (
                        item["lastest_commit"]["commit"]["author"]["name"]
                    ).decode().encode('utf-8').strip()
                }    
            )

        return list_of_repositories

    def renderTemplate(self, data, search_term):
        return self.template.render(
            search_term=search_term, 
            list_of_repositories=self.parseBody(
                data
            )
        )
        


def processRequest(requestURL):
    GET_request_obtained_data = []
    try:
        GET_request_processed = requests.get(
            url = requestURL
        )
    except requests.exceptions.Timeout:
        print("***[EXCEPTION]*** [processRequest] Request Timeout")
    except requests.exceptions.TooManyRedirects:
        print("***[EXCEPTION]*** [processRequest] Request TooManyRedirects")
    except requests.exceptions.RequestException as e:
        print("***[EXCEPTION]*** [processRequest] Request RequestException"
            + '\nError: ' 
            + str(e)
        )
    except Exception as e:
        print("***[EXCEPTION]*** [processRequest] Request Exception"
            + '\nError: ' 
            + str(e)
        )
    else:
        GET_request_obtained_data = GET_request_processed
    finally:
        return GET_request_obtained_data

def fetchLastestCommit(repository):
    global GLOBAL_LIST_OF_PARSED_COMMITS

    GET_request_data_sorted = []
    endpoint_URL = GITHUB_COMMITS_REPOSITORY_URL % {
        'owner_name': repository["owner"]["login"],
        'repository_name': repository["name"]
    }

    GET_request_processed = processRequest(
        endpoint_URL
    )
    GET_request_data_sorted = GET_request_processed.json()[0]
    repository["lastest_commit"] = GET_request_data_sorted
    
    GLOBAL_LIST_OF_PARSED_COMMITS.append(
        repository
    )

def fetchRepositories(search_term):
    
    # Setting up default data
    GET_request_data_sorted = []
    
    # Preparing URL
    endpoint_URL = GITHUB_SEARCH_REPOSITORY_URL % {
        'search_term': search_term
    }

    # Fetching repositories
    GET_request_processed = processRequest(endpoint_URL).json()

    # Making sure, that the list of processed items is not empty
    if(len(GET_request_processed["items"]) > 0):
        
        '''
            Sorting received repositories &
            slicing the array in order to receive needed amount of elements &
            linking each and every chosen repository with its lastest commit 
        '''
        threads = [ ]

        try:

            for fetchedRepository in sorted( 
                    GET_request_processed["items"]
                    , key=lambda x: x["created_at"]
                    , reverse=True
                )[0:NUMBER_OF_RENDERED_REPOSITORIES]:

                t = threading.Thread(
                    target=fetchLastestCommit, 
                    args=(fetchedRepository,)
                )

                threads.append(
                    t
                )
                t.start()

            for one_thread in threads:
                one_thread.join()

        except Exception as e:
            print("***[EXCEPTION]*** [fetchRepositories] Something went wrogn when processing repositories"
                + '\nerror: ' 
                + str(e)
            )

    return GET_request_data_sorted

def application (environ, start_response):
    global GLOBAL_LIST_OF_PARSED_COMMITS

    response_body = ''

    # Parsing query string
    d = parse_qs(
        environ['QUERY_STRING']
    )

    # Escaping dangerous characters
    search_term = escape(
        d.get(
            'search_term', ['']
        )[0]
    ) 


    if(
        len(
            search_term
            ) > 0
        ):

        # Fetching repostories & linking it with the commits
        fetchRepositories(
            search_term
        )

        # Creating default template object
        template = TemplateParser()

        # Matching receivd data with proper values
        # marked in the .html template
        response_body = template.renderTemplate(
            GLOBAL_LIST_OF_PARSED_COMMITS, 
            search_term
        )

        status = '200 OK'
    else:
        status = '404 NOT FOUND'

    # Now content type is text/html
    response_headers = [
        ('Content-Type', 'text/html'),
        ('Content-Length', str(len(response_body)))
    ]

    start_response(
        status, response_headers
    )
    
    GLOBAL_LIST_OF_PARSED_COMMITS = []

    return [
        response_body.encode("utf-8")
    ]

httpd = make_server('localhost', 8051, application)
httpd.serve_forever()