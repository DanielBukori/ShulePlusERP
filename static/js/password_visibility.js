(function () {
  const eyeIcon = '<svg viewBox="0 0 24 24" aria-hidden="true" style="width:1.25rem;height:1.25rem;fill:none;stroke:currentColor;stroke-width:1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M2.5 12s3.5-7 9.5-7 9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7z"/><circle cx="12" cy="12" r="3"/></svg>';
  const eyeOffIcon = '<svg viewBox="0 0 24 24" aria-hidden="true" style="width:1.25rem;height:1.25rem;fill:none;stroke:currentColor;stroke-width:1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M9.9 5.2A9.7 9.7 0 0112 5c6 0 9.5 7 9.5 7a16 16 0 01-3.1 3.8M6.2 6.2C3.8 7.8 2.5 12 2.5 12s3.5 7 9.5 7a9.7 9.7 0 004-.8"/></svg>';

  document.querySelectorAll('input[type="password"]').forEach(function (input, index) {
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    input.style.paddingRight = '2.75rem';

    const button = document.createElement('button');
    button.type = 'button';
    button.setAttribute('aria-label', 'Onyesha nywila');
    button.setAttribute('aria-pressed', 'false');
    button.setAttribute('aria-controls', input.id || 'password-field-' + index);
    if (!input.id) input.id = 'password-field-' + index;
    button.title = 'Onyesha nywila';
    button.innerHTML = eyeIcon;
    button.style.cssText = 'position:absolute;right:0.5rem;top:50%;transform:translateY(-50%);display:flex;align-items:center;justify-content:center;padding:0.375rem;border:0;background:transparent;color:#475569;cursor:pointer;';

    button.addEventListener('click', function () {
      const showPassword = input.type === 'password';
      input.type = showPassword ? 'text' : 'password';
      button.setAttribute('aria-label', showPassword ? 'Ficha nywila' : 'Onyesha nywila');
      button.setAttribute('aria-pressed', String(showPassword));
      button.title = showPassword ? 'Ficha nywila' : 'Onyesha nywila';
      button.innerHTML = showPassword ? eyeOffIcon : eyeIcon;
    });

    wrapper.appendChild(button);
  });
})();
