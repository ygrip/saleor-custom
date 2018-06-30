import 'lazysizes';
import SVGInjector from 'svg-injector-2';

export const getAjaxError = (response) => {
  const ajaxError = $.parseJSON(response.responseText).error.quantity;
  return ajaxError;
};
export const csrftoken = $.cookie('csrftoken');

export default $(document).ready((e) => {
  function csrfSafeMethod(method) {
    return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
  }

  new SVGInjector().inject(document.querySelectorAll('svg[data-src]'));

  $.ajaxSetup({
    beforeSend (xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      }
    },
  });

  // Open tab from the link

  const hash = window.location.hash;
  $(`.nav-tabs a[href="${hash}"]`).tab('show');

  // Preload all images
  window.lazySizesConfig.preloadAfterLoad = true;
});
