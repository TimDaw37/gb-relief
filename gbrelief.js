/* GB Relief base map for Leaflet (https://timdaw37.github.io/gb-relief/)
   <script src="https://timdaw37.github.io/gb-relief/gbrelief.js"></script>
   GBRelief.layer('relief').addTo(map);          // 'relief', 'grey' or 'geology'
   Set the map container's background to GBRelief.SEA: the sea in the tiles is transparent. */
(function (g) {
  var BASE = 'https://timdaw37.github.io/gb-relief/tiles/';
  var ATTR = 'Relief: <a href="https://timdaw37.github.io/gb-relief/">GB Relief</a> (Tim Daw, CC BY 4.0) from ' +
    'Environment Agency, Welsh Government and Scottish Government LiDAR (OGL); GEM-15 &copy; Google (CC BY 4.0); ' +
    'OS Open Zoomstack &copy; Crown copyright and database right 2026';
  var GEOL = '; geology: BGS Geology 625k &copy; UKRI (OGL)';
  g.GBRelief = {
    SEA: '#d6e2e8',
    bounds: [[49.7, -8.8], [61.0, 2.0]],
    layer: function (style, opts) {
      style = style || 'relief';
      var o = { minZoom: 5, maxNativeZoom: 11, maxZoom: 19, bounds: this.bounds,
        attribution: ATTR + (style === 'geology' ? GEOL : '') };
      for (var k in (opts || {})) o[k] = opts[k];
      return L.tileLayer(BASE + style + '/{z}/{x}/{y}.webp', o);
    }
  };
})(window);
