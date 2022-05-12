const Regions = require('./vdd-regions.js')

const ctx = {}
const items = []

for (const proviceName in Regions.provinces) {
  const provinceId = `/geo/Sverige/${encodeURIComponent(proviceName)}`
  const proviceRef = {'@id': provinceId}
  const locatedIn = []
  items.push({
    '@id': provinceId,
    '@type': 'Place',
    label: proviceName,
    '@reverse': {
      locatedIn: locatedIn
    }
  })
  for (const region of Regions.provinces[proviceName]) {
    const regionId = `${provinceId}/${encodeURIComponent(region.name)}`
    ctx[region.index] = regionId
    locatedIn.push({
      '@id': regionId,
      '@type': 'ARegion',
      label: region.name,
      code: region.index
    })
  }
}

console.log(JSON.stringify({'@context': ctx, '@graph': items}, null, 2))
