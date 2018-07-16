import 'ez-plus';
import 'lightgallery';
import 'lg-thumbnail';
import 'lg-fullscreen';
import 'lg-autoplay';
import 'lg-zoom';
import 'picturefill';

const randomColor = require('randomcolor');

console.log('image-zoomer module loaded');

$(document).ready(() => {
  let $count = 0;
  const $current = 0;
  const $custom_item = $('#lightgallery');
  $('.carousel-item').each((i, obj) => {
	    // test
    $count++;
  });
  

  renderZoomer();

  const baseColor = randomColor({ hue: 'blue' });
  const color = randomColor({
    count: $count, luminosity: 'dark', format: 'rgba', hue: baseColor, alpha: 0.3,
  });

  $custom_item.lightGallery({
    thumbnail: true,
    animateThumb: false,
   		showThumbByDefault: false,
    mode: 'lg-fade',
  });

  $('.lg-outer').css({ transition: 'background-color 600ms ease 0s' });

  $custom_item.on('onBeforeSlide.lg', (event, prevIndex, index) => {
	    $('.lg-outer').css('background-color', color[index]);
  });

  $('#carousel-example-generic').on('slide.bs.carousel', () => {
    $('.zoomContainer').remove();
    $('.image-details').removeData('ezPlus');
    renderZoomer();
  });
});

function renderZoomer() {
  $('.image-details').ezPlus({
    zoomType: 'lens',
	    lensShape: 'round',
	    containLensZoom: true,
	    lensSize: 150,
    scrollZoom: true,
    responsive: true,
  });
}

