def to_filename(course):
    return course.replace('/','-').replace('.','_')

def module_name(axis, module_id):
    mid = module_id.replace('.','_')
    module = axis[axis.module_id == mid]
    if module.empty:
        name = ''
    else:
        name = module.iloc[0,:]['name']
        if name == '':
            name = ''
            
    return name.replace('/', ' ').replace('_', ' ')