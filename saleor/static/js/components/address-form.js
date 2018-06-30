export default $(document).ready((e) => {
  $(() => {
    const $i18nAddresses = $('.i18n-address');
    $i18nAddresses.each(function () {
      const $form = $(this).closest('form');
      const $countryField = $form.find('select[name=country]');
      const $previewField = $form.find('input.preview');
      $countryField.on('change', () => {
        $previewField.val('on');
        $form.submit();
      });
    });
  });

  const $deleteAdressIcons = $('.icons');
  const $deleteAdressIcon = $('.delete-icon');
  const $deleteAddress = $('.address-delete');

  $deleteAdressIcon.on('click', (e) => {
    if ($deleteAddress.hasClass('none')) {
      $deleteAddress.removeClass('none');
      $deleteAdressIcons.addClass('none');
    } else {
      $deleteAddress.addClass('none');
    }
  });

  $deleteAddress.find('.cancel').on('click', (e) => {
    $deleteAddress.addClass('none');
    $deleteAdressIcons.removeClass('none');
  });

  // New address dropdown

  const $addressShow = $('.address_show label');
  const $addressHide = $('.address_hide label');
  const $addressForm = $('.checkout__new-address');
  const $initialValue = $('#address_new_address').prop('checked');
  $addressShow.click((e) => {
    $addressForm.slideDown('slow');
  });
  $addressHide.click((e) => {
    $addressForm.slideUp('slow');
  });
  if ($initialValue) {
    $addressForm.slideDown(0);
  } else {
    $addressForm.slideUp(0);
  }
});
