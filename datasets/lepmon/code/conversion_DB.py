import csv

class FieldTracker:
    def __init__(self, columns):
        self.values = {col: None for col in columns}
        self.set_flags = {col: False for col in columns}

    def set(self, col, value):
        if col in self.values:
            self.values[col] = value
            self.set_flags[col] = True

    def is_set(self, col):
        return self.set_flags.get(col, False)

    def __repr__(self):
        lines = []
        for col in self.values:
            val = self.values[col]
            flag = self.set_flags[col]
            lines.append(f"{col}: {val!r} (set: {flag})")
        return "\n".join(lines)

class CamtrapDPFields:
    def __init__(self, headers_dict):
        self.deployments = FieldTracker(headers_dict['deployments'])
        self.media = FieldTracker(headers_dict['media'])
        self.observations = FieldTracker(headers_dict['observations'])

# Beispiel: Header aus CSV einlesen
def get_csv_header(filepath):
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        return next(reader)

def write_fields_to_csv(field_tracker, output_path):
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(field_tracker.values.keys()))
        writer.writeheader()
        writer.writerow(field_tracker.values)

def append_fields_to_csv(field_tracker, output_path):
    file_exists = False
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            file_exists = True
    except FileNotFoundError:
        pass
    with open(output_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(field_tracker.values.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(field_tracker.values)

def log_unset_fields(field_tracker, log_path, category_name):
    unset = [col for col, flag in field_tracker.set_flags.items() if not flag]
    if unset:
        import csv
        write_header = False
        try:
            with open(log_path, 'r', encoding='utf-8') as logfile:
                if logfile.readline() == '':
                    write_header = True
        except FileNotFoundError:
            write_header = True
        with open(log_path, 'a', newline='', encoding='utf-8') as logfile:
            writer = csv.writer(logfile)
            if write_header:
                writer.writerow(['category', 'unset_fields'])
            writer.writerow([category_name, ';'.join(unset)])

def write_config_template(field_tracker, output_path):
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['field', 'filepath', 'column'])
        for col in field_tracker.values.keys():
            writer.writerow([col, '', ''])

def write_config_template_all(fields_obj, output_path):
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['category', 'field', 'filepath', 'column'])
        for category in ['deployments', 'media', 'observations']:
            tracker = getattr(fields_obj, category)
            for col in tracker.values.keys():
                writer.writerow([category, col, '', ''])
    print(f"Config template '{output_path}' created. Please fill in the file paths and columns, then run the script again.")

def read_config_and_assign_fields(field_tracker, config_path):
    with open(config_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            field = row['field']
            filepath = row['filepath']
            column = row['column']
            if filepath and column:
                # Hole Wert aus Datei/Spalte
                with open(filepath, newline='', encoding='utf-8') as f:
                    csvreader = csv.DictReader(f)
                    for data_row in csvreader:
                        if column in data_row:
                            value = data_row[column]
                            field_tracker.set(field, value)
                            break  # Nur ersten Wert nehmen

def read_config_and_assign_fields_all_per_row(fields_obj, config_path, row_dict):
    with open(config_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category = row['category']
            field = row['field']
            filepath = row['filepath']
            column = row['column']
            if filepath and column and category in ['deployments', 'media', 'observations']:
                tracker = getattr(fields_obj, category)
                # Wenn filepath als Platzhalter für die aktuelle Datei dient
                if filepath == 'data_infiltratie_c231_2025.csv':
                    value = row_dict.get(column, None)
                    if value is not None:
                        tracker.set(field, value)
                else:
                    with open(filepath, newline='', encoding='utf-8') as f:
                        csvreader = csv.DictReader(f)
                        for data_row in csvreader:
                            if column in data_row:
                                value = data_row[column]
                                tracker.set(field, value)
                                break

if __name__ == "__main__":
    headers = {
        'deployments': get_csv_header("../example-datasets/deployments_template.csv"),
        'media': get_csv_header("../example-datasets/media_template.csv"),
        'observations': get_csv_header("../example-datasets/observations_template.csv"),
    }
    fields = CamtrapDPFields(headers)

    create_config = input("Do you want to set a new configuration file? (yes/no): ").strip().lower()
    if create_config == 'yes':
        write_config_template_all(fields, 'fields_config.csv')
    else:
        cont = input("Do you want to continue? (yes/no): ").strip().lower()
        if cont == 'yes':
            with open('data_infiltratie_c231_2025.csv', newline='', encoding='utf-8') as infil:
                infil_reader = csv.DictReader(infil)
                for idx, row in enumerate(infil_reader):
                    fields = CamtrapDPFields(headers)
                    read_config_and_assign_fields_all_per_row(fields, 'fields_config.csv', row)
                    print(f'--- Row {idx+1} ---')
                    print('--- Deployments ---')
                    print(fields.deployments)
                    print('--- Media ---')
                    print(fields.media)
                    print('--- Observations ---')
                    print(fields.observations)
                    append_fields_to_csv(fields.deployments, 'deployments_output.csv')
                    append_fields_to_csv(fields.media, 'media_output.csv')
                    append_fields_to_csv(fields.observations, 'observations_output.csv')
                    log_unset_fields(fields.deployments, 'unset_fields.log', f'deployments_row_{idx+1}')
                    log_unset_fields(fields.media, 'unset_fields.log', f'media_row_{idx+1}')
                    log_unset_fields(fields.observations, 'unset_fields.log', f'observations_row_{idx+1}')
        else:
            print("abort.")



