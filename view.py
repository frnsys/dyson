style = '''
html, body {
    margin: 0 auto;
    padding: 0;
    background: #111111;
    color: #fff;
    font-family: sans-serif;
    max-width: 900px;
}
ul, li {
    margin: 0;
    padding: 0;
    list-style-type: none;
}
ul {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
}
section {
    padding: 1em;
}
figure {
    margin: 0;
    position: relative;
    display: inline-block;
}
img {
    border: 1px solid #fff;
    box-shadow: 2px 2px #ebebeb;
}
h2 {
    font-size: 1.2em;
    font-weight: normal;
}
p {
    margin: 0;
    font-size: 0.8em;
}
li {
    width: 150px;
    margin-bottom: 2em;
}
figcaption {
    position: absolute;
    right: 0;
    top: 0;
    padding: 1em;
    font-size: 0.6em;
    font-family: monospace;
}
'''

html = '''
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>dyson</title>
        <style>{style}</style>
    </head>
    <body>{body}</body>
</html>
'''

section = '''
<section>
    <h2>{title}</h2>
    <ul>{items}</ul>
</section>
'''

item = '''
<li>
    <figure>
        <img src="{src}">
        <figcaption>{coords}</figcaption>
    </figure>
    <p>{desc}</p>
</li>
'''


def make_site(groups, outfile):
    sections = []
    for name, feats in groups.items():
        items = []
        for feat in feats:
            props = feat['properties']
            items.append(item.format(
                src=feat['img'],
                coords='<br />'.join([str(c) for c in feat['geometry']['coordinates']]),
                desc='<br />'.join(props['description'])
            ))
        sections.append(section.format(
            title=name,
            items='\n'.join(items)
        ))
    with open(outfile, 'w') as f:
        f.write(html.format(
            style=style,
            body='\n'.join(sections)))


if __name__ == '__main__':
    import json
    from main import feats

    # Generate site
    dataset = json.load(open('data/dataset.json'))
    groups = {name: [] for name in feats.keys()}
    for imgid, data in dataset.items():
        groups[data['type']].append(data)

    make_site(groups, 'data/index.html')
