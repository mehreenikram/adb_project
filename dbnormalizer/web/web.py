__author__ = 'Maira'
from flask import Flask, render_template, request, make_response
import webbrowser
import threading
import time
from dbnormalizer.core.importdata.XMLImport import XMLImport
from dbnormalizer.core.importdata.DBImport import DBImport
import json
from dbnormalizer.core.util.funcs import get_attributes_list, get_fds_list
from dbnormalizer.core.table.FD import FD
from dbnormalizer.core.normalizer.NF import NF
from dbnormalizer.core.normalizer.normalizer import Normalizer
from dbnormalizer.core.importdata.manualImport import ManualImport
from dbnormalizer.core.table.schema import Schema
from dbnormalizer.core.util.DBGenerateScript import DBGenerateScript
from dbnormalizer.core.util.XMLExport import XMLExport

app = Flask(__name__)
schema = []
db_c = None
normalized_schemas = {}
db_connection = {}

def open_browser():
    """
    opens the browser for "gui"
    """
    time.sleep(2)
    url = "http://localhost:5000"
    webbrowser.open(url)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/<button>")
def click(button):
    """
    Simple button click, only with GET
    :param button: the domId of the button that was clicked
    :return:
    """
    print(button)
    try:
        if button == 'downloadSQL':
            decomposition_type = request.args['type']
            table_name = request.args['table']
            new_schema = {}
            if decomposition_type == '3NF' or decomposition_type == '3nf':
                new_schema = normalized_schemas[table_name].get_nf3_schema()
            elif decomposition_type == 'BCNF' or decomposition_type == 'bcnf':
                new_schema = normalized_schemas[table_name].get_bcnf_schema()
            old_schema = Schema(schema.name)
            table_obj = schema.get_table_by_name(table_name)
            old_schema.add_table(table_obj)
            new_schema.name = old_schema.name
            gen = DBGenerateScript(new_schema, old_schema, db_c['username'], db_c['pwd'], db_c['url'], db_c['db'])
            file = gen.generate_script()
            response = make_response(file)
            response.headers["Content-Disposition"] = "attachment; filename="+table_name+"_decomposition.sql"
            return response
        elif button == 'XMLDownload':
            xml_export = XMLExport(schema)
            xml_file = xml_export.generate_xml()
            response = make_response(xml_file)
            response.headers["Content-Disposition"] = "attachment; filename="+schema.get_name+".xml"
            return response
        return "test"
    except Exception as e:
        print(e)


@app.route("/<button>", methods=["POST"])
def upload(button):
    """
    Upload handler
    :param button: the domId of the button that was clicked
    :return:
    """
    global schema
    global db_structure
    global normalized_schemas
    global db_c
    print(button)
    try:
        if button == "xmlButton":
            xml_data = request.form["data"]
            xml_structure = XMLImport(xml_data, False)
            xml_structure.init_objects()
            db_structure = None
            schema = xml_structure.get_schema()
            js_object = get_display_tables_js_object()
            return js_object
        elif button == "insertDBButton":
            url = request.form.get('url')
            username = request.form.get('user')
            pwd = request.form.get('pwd')
            db_name = request.form.get('dbName')
            schema_name = request.form.get('schema')
            db_c = {
                'url': url,
                'username': username,
                'pwd': pwd,
                'db':db_name
            }
            db_structure = DBImport(url, username, pwd, schema_name, db_name)
            if None == db_structure.get_error():
                schema = db_structure.map_tables()
                js_object = get_display_tables_js_object()
                return js_object
            else:
                error = db_structure.get_error()
                return error
        elif button == "insertmanual":
            data = request.form.get('data')
            schema_data = json.loads(data)
            mi = ManualImport(schema_data)
            schema = mi.get_schema()
            js_object = get_display_tables_js_object()
            return js_object
        elif button == "requestFD" or button == "attributeClosure":
            table_name = request.form['table']
            attrs = schema.get_table_attributes(table_name)
            js_object = get_attr_list_js(attrs)
            return js_object
        elif button == "insertFDButton":
            table_name = request.form['table']
            lhs = []
            rhs = []
            lhs_list = request.form['lhs'].split(',')
            rhs_list = request.form['rhs'].split(',')
            table = schema.get_table_by_name(table_name)
            for l in lhs_list:
                lhs.append(table.get_attribute_by_name(l))
            for r in rhs_list:
                rhs.append(table.get_attribute_by_name(r))
            fd = FD(lhs, rhs)
            table.add_fd(fd)
            return "success"
        elif button == "editFDButton":
            table_name = request.form['table']
            lhs_list = request.form['lhs'].split(',')
            rhs_list = request.form['rhs'].split(',')
            lhs = []
            rhs = []
            fd_id = request.form['id']
            table = schema.get_table_by_name(table_name)
            for l in lhs_list:
                lhs.append(table.get_attribute_by_name(l))
            for r in rhs_list:
                rhs.append(table.get_attribute_by_name(r))
            fd = table.get_fd_by_id(int(fd_id))
            fd.set_lhs(lhs)
            fd.set_rhs(rhs)
            return "success"
        elif button == "removeFDButton":
            table_name = request.form['table']
            fd_lhs = request.form['lhs']
            fd_rhs = request.form['rhs']
            fds_lhs_list = fd_lhs.split(',')
            fds_rhs_list = fd_rhs.split(',')
            table = schema.get_table_by_name(table_name)
            table.delete_fds(fds_lhs_list, fds_rhs_list)
            return "success"
        elif button == "minimalCover":
            table_name = request.form['table']
            table = schema.get_table_by_name(table_name)
            nf = NF(table)
            mc = nf.get_min_cover()
            js_object = get_display_fd_js_object(mc)
            return js_object
        elif button == "getAttributeClosure":
            table_name = request.form['table']
            table = schema.get_table_by_name(table_name)
            attributes = []
            attr_list = request.form['attributes'].split(',')
            for attr in attr_list:
                attributes.append(table.get_attribute_by_name(attr))
            nf = NF(table)
            ac = nf.get_attr_closure(attributes)
            return get_attr_list_js(ac)
        elif button == "candidateKeys":
            table_name = request.form['table']
            table = schema.get_table_by_name(table_name)
            nf = NF(table)
            ck = nf.get_candidate_keys()
            return get_candidate_keys_js(ck)
        elif button == "normalForm":
            table_name = request.form['table']
            table = schema.get_table_by_name(table_name)
            nf = NF(table)
            current_nf = nf.determine_nf()
            violated_fd = nf.get_violating_fds()
            js_object = get_nf_js_object(current_nf, violated_fd)

            return js_object
        elif button == "checkfds":
            table_name = request.form['table']
            table = schema.get_table_by_name(table_name)
            fds_hold_object = db_structure.check_fds_hold(table.get_fds, table.get_name)
            js_object = get_hold_fds_js_object(fds_hold_object)
            return js_object
        elif button == "normalizer":
            table_name = request.form['table']
            table = schema.get_table_by_name(table_name)
            nf = NF(table)
            current_nf = nf.determine_nf()
            if current_nf == 'BCNF':
                return 'false'
            normalization = Normalizer(nf)
            normalization.decomposition()
            if normalization.get_nf3_is_not_bcnf():
                table_nf3 = normalization.get_new_tables_nf3()
                table_bcnf = normalization.get_new_tables_bcnf()
                normalized_schemas[table_name] = normalization
                js_object = get_normalized_tables_js_object({'3nf': table_nf3, 'bcnf': table_bcnf})
            else:
                table = normalization.get_new_tables_nf3()
                normalized_schemas[table_name] = normalization
                js_object = get_normalized_tables_js_object({'3nf': table})
            return js_object
        return "Undefined button: " + button
    except Exception as e:
        print(e)


def get_hold_fds_js_object(fds_hold_object):
    fds_hold = get_fds_list(fds_hold_object['hold'])
    fds_not_hold = get_fds_list(fds_hold_object['not_hold'])
    return json.dumps({'hold': fds_hold, 'not_hold': fds_not_hold})


def get_nf_js_object(nf, violated_fds):
    fds_obj = get_fds_list(violated_fds)
    return json.dumps({'nf': nf, 'violated_fds': fds_obj})


def get_candidate_keys_js(keys):
    js_object = []
    for key in keys:
        attr_list = []
        for attr in key:
            attr_list.append(attr.get_name)
        js_object.append(attr_list)
    return json.dumps(js_object)


def get_display_fd_js_object(fds):
    fds_obj = get_fds_list(fds)
    return json.dumps(fds_obj)


def get_display_tables_js_object():
    tables = schema.get_tables()
    tables_data = []
    for table in tables:
        attributes = get_attributes_list(table.get_attributes)
        fds = get_fds_list(table.get_fds)
        tables_data.append({
            'name': table.get_name,
            'attributes': attributes,
            'fds': fds
        })
    return json.dumps(tables_data)


def get_normalized_tables_js_object(tables):
    tables_data = {}
    if 'bcnf' in tables:
        tables_bcnf = tables['bcnf']
        tables_3nf = tables['3nf']
        tables_data['bcnf'] = []
        tables_data['3nf'] = []
        for table in tables_bcnf:
            table_structure = create_normalized_table_structure(table)
            tables_data['bcnf'].append(table_structure)
        for table in tables_3nf:
            table_structure = create_normalized_table_structure(table)
            tables_data['3nf'].append(table_structure)
    else:
        tables_3nf = tables['3nf']
        tables_data['3nf'] = []
        for table in tables_3nf:
            table_structure = create_normalized_table_structure(table)
            tables_data['3nf'].append(table_structure)
    return json.dumps(tables_data)


def create_normalized_table_structure(table):
    attributes = get_attributes_list(table.get_attributes)
    fds = get_fds_list(table.get_fds)
    f_keys = []
    for f_key in table.get_foreign_keys():
        f_k = {'attr': f_key.get_attr(),
               'referenced_table': f_key.get_referenced_table(),
               'referenced_attribute': f_key.get_referenced_attribute()}
        f_keys.append(f_k)
    t_nf = NF(table)
    cks = t_nf.get_candidate_keys()
    candidate_keys = []
    for ck in cks:
        ck_a = [a.get_name for a in ck]
        candidate_keys.append(ck_a)
    table_data = {
        'name': table.get_name,
        'attributes': attributes,
        'fds': fds,
        'f_key': f_keys,
        'candidate_keys': candidate_keys
    }
    return table_data


def get_attr_list_js(attributes):
    attr_list = []
    for attr in attributes:
        attr_list.append(attr.get_name)
    return json.dumps(attr_list)

if __name__ == "__main__":
    t = threading.Thread(target=open_browser)
    t.daemon = True
    t.start()
    app.run()
