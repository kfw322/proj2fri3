var myPlot = document.getElementById("myDiv");
Plotly.d3.csv('https://raw.githubusercontent.com/Sangjin135/Sangjin135.github.io/Lily/data.csv', function(err, rows){
function unpack(rows, key) {
return rows.map(function(row) { return row[key]; });
}
var data = [{
    type: 'choropleth',
    locationmode: 'USA-states',
    locations: unpack(rows, 'Code'),
    z: unpack(rows, '2016PCE'),
    text: unpack(rows, 'GeoName'),
    zmin: -10000,
    zmax: 1700000,
    colorscale: 'Hot',
    hoverinfo: "location+z+text",
  colorbar: {
    title: 'USD',
    thickness: 20
  },
  marker: {
    line:{
      color: 'rgb(0,0,0)',
      width: 2
    }
  }
}];
console.log(data.locations);
var layout = {
title: '2016 Personal Consumption Expenditure in the United States (In Millions)',
geo:{
  scope: 'usa',
  showlakes: true,
  lakecolor: 'rgb(255,255,255)'
}
};


Plotly.plot(myDiv, data, layout, {showLink: false});
myPlot.on("plotly_click", d => {
  var pt = (d.points || [])[0]
  window.open(
    'pcegraph/' + pt.text,
    '_blank' // <- This is what makes it open in a new window.
  );})

})