def multipleReturn():
    dict={'a': 2,
          'b': 4}
    list=[1,2,3]

    return dict, list

print(multipleReturn()[1])