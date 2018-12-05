import os
import string
from pymongo import MongoClient, ASCENDING


client = MongoClient(
    os.environ['DB_PORT_27017_TCP_ADDR'],
    27017)
# client = MongoClient("mongodb://localhost:27017")
db = client.classifier
root_folder = {'name': 'root', 'path': '/'}
if db.classifier.find(root_folder).count() == 0:
    db.classifier.insert_one(root_folder)


def delete_identifier(record):
    if '_id' in record:
        del record['_id']


def create_classifier(list_of_records):
    """
    Creates a nested dict classifier out of materialized path tree representation (list of records)
    """
    def insert_record(rec, cur_root):
        delete_identifier(rec)
        if not cur_root.get("sub"):
            cur_root["sub"] = []
        if rec["path"] == cur_root["path"] + cur_root['name'] + '/':
            cur_root["sub"].append(rec)
        else:
            for sub_root in cur_root["sub"]:
                insert_record(rec, sub_root)

    classifier = list_of_records[0]
    delete_identifier(classifier)
    for record in list_of_records[1:]:
        insert_record(record, classifier)
    return classifier


def bad_request_400():
    return 'invalid input', 400


def record_exist_409():
    return 'path not found or record already exist', 409


def record_not_found_404():
    return 'record not found', 404


def records_deleted_successfully_204():
    return 'record was deleted successfully', 204


def get_name_and_paths_from_request(request_body):
    name = request_body['name']
    path = request_body['path']
    if not path.endswith('/'):
        path += '/'
    if path.startswith('/root'):
        db_path = path
    else:
        db_path = f"/root{request_body['path']}"
    return name, path, db_path


def is_name_valid(name, path):
    """
    Valid name consists of only latin and cyrillic letters and numbers and one space between words. No other symbols
    can be used. Name must be unique into it's path
    """
    latin = string.ascii_letters
    russian = 'абвгдеёжзиклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    numbers = '0123456789'
    space = ' '
    total_readable = latin + russian + numbers
    allowed_readable = set(total_readable)
    if name == '' or name[0] not in allowed_readable:
        return False
    prev_space = False
    for letter in name:
        if letter not in allowed_readable:
            # check that space is only one
            if letter != space or prev_space:
                return False
            prev_space = True
            continue
        prev_space = False
    if name in path:
        return False
    return True


def is_record_exist(name, path):
    return db.classifier.find({'name': name, 'path': path}).count() > 0


def is_parent_exist(path):
    path_list = path.split('/')
    last_slash = path_list.pop()
    parent_name = path_list.pop()
    path_list.append(last_slash)
    parent_path = '/'.join(path_list)
    return db.classifier.find({'name': parent_name, 'path': parent_path}).count() > 0


def read(record_path='/'):
    """
    If no path given, returning the whole classifier. Otherwise - returning subclassifier.
    """
    if not record_path.endswith('/'):
        record_path += '/'
    records = []
    if record_path == '/':
        records.extend(db.classifier.find({}))
    else:
        path_list = record_path.split('/')
        last_slash = path_list.pop()
        name = path_list.pop()
        path_list.append(last_slash)
        parent_path = '/'.join(path_list)
        root_record = db.classifier.find({'name': name, 'path': f'/root{parent_path}'})
        records.extend(root_record)
        sub_records_path_reg = f"^/root{record_path}"
        records.extend(db.classifier.find({'path': {'$regex': sub_records_path_reg}}).sort('path', ASCENDING))
    response = create_classifier(records)
    return response


def add_record(body):
    """
    Adds record into classifier.
    Only valid records will be added. Only records which direct parents already exist can be added.
    """
    name, path, db_path = get_name_and_paths_from_request(body)
    if not is_name_valid(name, path):
        return bad_request_400()
    if not is_parent_exist(db_path) or is_record_exist(name, db_path):
        return record_exist_409()
    new_record = {'name': name, 'path': db_path}
    success = db.classifier.insert_one(new_record)
    answer = {'_id': str(success.inserted_id),  'name': name, 'path': path}
    return answer


def remove(body):
    """
    Removes given record and all it's subrecords/subclassifiers.
    """
    name, path, db_path = get_name_and_paths_from_request(body)
    if not is_name_valid(name, path):
        return bad_request_400()
    if not is_record_exist(name, db_path):
        return record_not_found_404()

    sub_records_path_reg = f'^{db_path}{name}/'
    subrecords_del_query = {'path': {'$regex': sub_records_path_reg}}
    db.classifier.delete_many(subrecords_del_query)

    record_del_query = {'name': name, 'path': db_path}
    db.classifier.delete_one(record_del_query)
    return


def create_updated_path(path, old_name, new_name):
    return path.replace(old_name, new_name)


def change_record(body):
    """
    Changes name of the given record and also updates all paths of it's subrecords/subclissifiers.

    """
    name, path, db_path = get_name_and_paths_from_request(body)
    new_name = body['new_name']
    if not is_name_valid(name, path):
        return bad_request_400()
    if not is_record_exist(name, db_path):
        return record_not_found_404()

    sub_records_path_reg = f'^{db_path}{name}/'
    subrecords_path_query = {'path': {'$regex': sub_records_path_reg}}
    collection = db.classifier.find(subrecords_path_query)
    for record in collection:
        old_path = record['path']
        new_path = old_path.replace(name, new_name)
        db.classifier.update_one({'path': old_path}, {'$set': {'path': new_path}})

    record_update_query = {'name': name, 'path': db_path}
    db.classifier.update_one(record_update_query, {'$set': {'name': new_name}})
    return
