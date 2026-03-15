from pokedata import load_data, search_by_name, filter_by_specialty, filter_by_favorite, related_by_habitat


def run():
    data = load_data('Pokopia.csv')
    assert data, 'no data loaded'
    res = search_by_name(data, 'Pikachu')
    print('search Pikachu ->', len(res))
    res2 = filter_by_specialty(data, 'Litter')
    print('filter specialty Litter ->', len(res2))
    res3 = filter_by_favorite(data, 'Soft stuff')
    print('filter favorite Soft stuff ->', len(res3))
    if res:
        rel = related_by_habitat(data, res[0])
        print('related to first result ->', len(rel))


if __name__ == '__main__':
    run()
