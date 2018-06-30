export default $(document).ready(() => {
  const styleGuideMenu = $('.styleguide__nav');
  $(window).scroll(function () {
    if ($(this).scrollTop() > 100) {
      styleGuideMenu.addClass('fixed');
    } else {
      styleGuideMenu.removeClass('fixed');
    }
  });
});
