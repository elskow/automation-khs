def get_specific_semester(data, semester):
    """Gets the data of a specific semester."""
    temp_data = data[str(semester)]["data"]
    filtered_data = [
        {
            "nm_mk": d.get("nm_mk", "n/a"),
            "nilai_huruf": d.get("nilai_huruf", "n/a")
            if d.get("nilai_huruf")
            else "n/a",
        }
        for d in temp_data
    ]
    return filtered_data


def what_lastest_semester(data):
    """Gets the lastest semester."""
    return max([int(semester) for semester in data.keys()])
