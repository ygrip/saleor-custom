import 'slider-pro';
import * as Vibrant from 'node-vibrant';

$(() => {
  $('#home-slider').sliderPro({
    width: '150%',
    height: 450,
    arrows: true,
    autoplayOnHover: false,
    waitForLayers: true,
    fade: true,
    autoplay: true,
    autoScaleLayers: true,
    keyboardOnlyOnFocus: true,
    imageScaleMode: 'contain',
    centerImage: true,
    orientation: 'horizontal',
    loop: true,
    buttons: false,
    breakpoints: {
      500: {
        height: 350,
        width: '60%',
        arrows: false,
      },
    },
    init(event) {
      const element = this.getSlideAt(0);
      const image_path = element.$mainImage['0'].dataset.default;
      const opts = {
        colorCount: 1,
        quality: 1,
      };

      const v = Vibrant.from(image_path, opts);
      v.getPalette((err, palette) => setColor(palette.Muted._rgb.toString()));
    },
    gotoSlideComplete(event) {
      const element = this.getSlideAt(event.index);
      const image_path = element.$mainImage['0'].dataset.default;
      const opts = {
        colorCount: 1,
        quality: 1,
      };

      const v = Vibrant.from(image_path, opts);
      v.getPalette((err, palette) => setColor(palette.DarkVibrant._rgb.toString()));
    },
  });
});

function setColor(color) {
  color = `rgba(${color},.9)`;
  $('.sp-image-container').css('background', color);
}
