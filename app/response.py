def success(data, message):
    return {"success": True, "message": message, "data": data}, 200

def error(data, message):
    return {"success": False, "message": message, "data": data}, 400
