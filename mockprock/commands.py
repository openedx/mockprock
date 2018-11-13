"""Command line utilities"""
from __future__ import print_function
import argparse
from mockprock.backend import MockProckBackend


def get_url():
    """
    Prints or opens an instructor dashboard url
    """
    parser = argparse.ArgumentParser(description='Return an instructor dashboard url')
    parser.add_argument("client_id", type=str, help="mockprock oauth client id", nargs="?", default='client')
    parser.add_argument("client_secret", type=str, help="mockprock oauth client secret", nargs="?", default='clientsecret')
    parser.add_argument('-o', dest='open_url', help='Open in browser', default=False, action='store_true')
    parser.add_argument('-c', dest='course_id', type=str, help='Course ID', required=True)
    args = parser.parse_args()
    course_id = args.course_id
    user = {
        'id': 1,
        'full_name': 'Course Instructor',
        'email': 'instructor@example.com',
    }
    backend = MockProckBackend(args.client_id, args.client_secret)
    url = backend.get_instructor_url(course_id, user)
    if args.open_url:
        print('Opening %s' % url)
        import webbrowser
        webbrowser.open(url)
    else:
        print(url)
