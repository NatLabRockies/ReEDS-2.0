$(document).ready(function(){
    $('body').on('click', '.reeds-vars-dropdown', function(){
        $('.reeds-vars-drop').toggle();
    });
    $('body').on('click', '.meta-dropdown', function(){
        $('.meta-drop').toggle();
    });
    $('body').on('click', '.data-dropdown', function(){
        $('.data-drop').toggle();
    });
    $('body').on('click', '.wdgkey-runs label, .wdgkey-result label, .wdgkey-presets label', function(){
        $(this).next().toggle();
    });
    $('body').on('click', '.scenario-filter-dropdown', function(){
        $('.scenario-filter-drop').toggle();
    });
    $('body').on('click', '.filter-head', function(){
        $(this).next().toggle();
        $(this).next().next().toggle();
        $(this).next().next().next().toggle();
    });
    $('body').on('click', '.report-dropdown', function(){
        $('.report-drop').toggle();
    });
    $('body').on('click', '.chart-dropdown', function(){
        $('.chart-drop').toggle();
    });
    $('body').on('click', '.x-dropdown', function(){
        $('.x-drop').toggle();
    });
    $('body').on('click', '.y-dropdown', function(){
        $('.y-drop').toggle();
    });
    $('body').on('click', '.series-dropdown', function(){
        $('.series-drop').toggle();
    });
    $('body').on('click', '.explode-dropdown', function(){
        $('.explode-drop').toggle();
    });
    $('body').on('click', '.adv-dropdown', function(){
        $('.adv-drop').toggle();
    });
    $('body').on('click', '.update-dropdown', function(){
        $('.update-drop').toggle();
    });
    $('body').on('click', '.download-dropdown', function(){
        $('.download-drop').toggle();
    });
    $('body').on('click', '.legend-dropdown', function(){
        $('.legend-drop').toggle();
    });
    $('body').on('click', '.filters-dropdown', function(){
        $('.filter-head').toggle();
        $('.filters-update').toggle();
        $('.filter-drop').hide();
    });
    $('body').on('click', '.adjust-dropdown', function(){
        $('.adjust-drop').toggle();
    });
    $('body').on('click', '.map-dropdown', function(){
        $('.map-drop').toggle();
    });
});
//pressing Alt key will collapse menus.
document.onkeydown = function(e) {
  if(e.which == 18) {
    $('.data-drop').hide();
    $('.reeds-vars-drop').hide();
    $('.meta-drop').hide();
    $('.report-drop').hide();
    $('.wdgkey-runs input').hide();
    $('.wdgkey-result select').hide();
    $('.wdgkey-presets select').hide();
    $('.chart-drop').hide();
    $('.scenario-filter-drop').hide();
    $('.x-drop').hide();
    $('.y-drop').hide();
    $('.legend-drop').hide();
    $('.series-drop').hide();
    $('.explode-drop').hide();
    $('.adv-drop').hide();
    $('.filter-head').hide();
    $('.filters-update').hide();
    $('.filter-drop').hide();
    $('.adjust-drop').hide();
    $('.map-drop').hide();
    $('.update-drop').hide();
    $('.download-drop').hide();
  }
};