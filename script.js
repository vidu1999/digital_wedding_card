document.documentElement.classList.add('js');

const wedding = {
  title: 'Anjali & Kavindu — Wedding Celebration',
  start: new Date('2027-03-06T18:00:00+05:30'),
  end: new Date('2027-03-06T23:00:00+05:30'),
  location: 'The Kingsbury, 48 Janadhipathi Mawatha, Colombo 01, Sri Lanka',
  description: 'Join us for our Poruwa ceremony, followed by dinner, music and dancing.'
};

const toast = document.getElementById('toast');
let toastTimer;
function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('is-visible');
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove('is-visible'), 3200);
}

// Mobile navigation
const siteHeader = document.querySelector('.site-header');
const menuToggle = document.querySelector('.menu-toggle');
const primaryNav = document.getElementById('primary-nav');
function closeMenu() {
  if (!siteHeader || !menuToggle) return;
  siteHeader.classList.remove('nav-open');
  menuToggle.setAttribute('aria-expanded', 'false');
  menuToggle.setAttribute('aria-label', 'Open navigation');
}
if (menuToggle && siteHeader) {
  menuToggle.addEventListener('click', () => {
    const isOpen = siteHeader.classList.toggle('nav-open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
    menuToggle.setAttribute('aria-label', isOpen ? 'Close navigation' : 'Open navigation');
  });
  primaryNav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
  document.addEventListener('click', (event) => {
    if (siteHeader.classList.contains('nav-open') && !siteHeader.contains(event.target)) closeMenu();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });
}

// RSVP dialog and local preview submission
const rsvpDialog = document.getElementById('rsvp-dialog');
const rsvpForm = document.getElementById('rsvp-form');
const successState = document.getElementById('success-state');
const guestDetails = document.getElementById('guest-details');
const successName = document.getElementById('success-name');
const successMessage = document.getElementById('success-message');

document.querySelectorAll('[data-open-rsvp]').forEach((button) => {
  button.addEventListener('click', () => {
    closeMenu();
    if (rsvpDialog?.showModal && !rsvpDialog.open) rsvpDialog.showModal();
  });
});
document.querySelectorAll('[data-close-rsvp]').forEach((button) => {
  button.addEventListener('click', () => rsvpDialog?.close());
});
rsvpDialog?.addEventListener('click', (event) => {
  if (event.target === rsvpDialog) rsvpDialog.close();
});

document.querySelectorAll('input[name="attendance"]').forEach((input) => {
  input.addEventListener('change', () => {
    const isAttending = document.querySelector('input[name="attendance"]:checked')?.value === 'yes';
    if (guestDetails) guestDetails.hidden = !isAttending;
  });
});

rsvpForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(rsvpForm);
  const name = String(formData.get('name') || '').trim();
  const firstName = name.split(/\s+/)[0] || 'friend';
  const attendance = String(formData.get('attendance') || 'yes');
  const response = {
    name,
    attendance,
    guests: attendance === 'yes' ? Number(formData.get('guests') || 1) : 0,
    dietary: attendance === 'yes' ? String(formData.get('dietary') || '').trim() : '',
    savedAt: new Date().toISOString()
  };
  try {
    localStorage.setItem('anjali-kavindu-wedding-rsvp', JSON.stringify(response));
  } catch (error) {
    // The thank-you screen still works if local storage is unavailable.
  }
  if (successName) successName.textContent = firstName;
  if (successMessage) {
    successMessage.textContent = attendance === 'yes'
      ? 'We’re so glad you’ll be there. We can’t wait to celebrate with you.'
      : 'Thank you for letting us know. You’ll be with us in spirit.';
  }
  rsvpForm.hidden = true;
  if (successState) successState.hidden = false;
});

// Add the wedding to Apple Calendar, Google Calendar, Outlook or any ICS-compatible app.
function icsEscape(value) {
  return String(value).replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/,/g, '\\,').replace(/;/g, '\\;');
}
function utcStamp(date) {
  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
}
document.querySelectorAll('[data-calendar]').forEach((button) => {
  button.addEventListener('click', () => {
    const now = utcStamp(new Date());
    const eventId = 'anjali-kavindu-20270306@wedding-invitation';
    const eventLines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Anjali and Kavindu//Wedding Invitation//EN',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      `UID:${eventId}`,
      `DTSTAMP:${now}`,
      `DTSTART:${utcStamp(wedding.start)}`,
      `DTEND:${utcStamp(wedding.end)}`,
      `SUMMARY:${icsEscape(wedding.title)}`,
      `LOCATION:${icsEscape(wedding.location)}`,
      `DESCRIPTION:${icsEscape(wedding.description)}`,
      'END:VEVENT',
      'END:VCALENDAR'
    ].join('\r\n');
    const blob = new Blob([eventLines], { type: 'text/calendar;charset=utf-8' });
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'Anjali-and-Kavindu-Wedding.ics';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
    showToast('The wedding date is ready to add to your calendar.');
  });
});

// Share from a device that supports the Web Share API, or copy the invitation URL.
document.querySelectorAll('[data-share]').forEach((button) => {
  button.addEventListener('click', async () => {
    const shareData = {
      title: wedding.title,
      text: 'Join Anjali & Kavindu in Colombo on 6 March 2027.',
      url: window.location.href
    };
    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (error) {
        if (error?.name !== 'AbortError') showToast('Sharing isn’t available right now.');
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(window.location.href);
      showToast('Invitation link copied to your clipboard.');
    } catch (error) {
      showToast('Copy this page’s URL to share the invitation.');
    }
  });
});

// Countdown uses the event's Sri Lanka Standard Time offset (+05:30).
const countdown = document.getElementById('countdown');
if (countdown) {
  const eventDate = new Date(countdown.dataset.eventDate);
  const daysNode = countdown.querySelector('[data-days]');
  const hoursNode = countdown.querySelector('[data-hours]');
  const minutesNode = countdown.querySelector('[data-minutes]');
  const secondsNode = countdown.querySelector('[data-seconds]');
  const messageNode = document.getElementById('countdown-message');
  const updateCountdown = () => {
    const remaining = eventDate.getTime() - Date.now();
    if (remaining <= 0) {
      if (daysNode) daysNode.textContent = '000';
      if (hoursNode) hoursNode.textContent = '00';
      if (minutesNode) minutesNode.textContent = '00';
      if (secondsNode) secondsNode.textContent = '00';
      if (messageNode) messageNode.textContent = 'Our celebration is here';
      return;
    }
    const totalSeconds = Math.floor(remaining / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    if (daysNode) daysNode.textContent = String(days).padStart(3, '0');
    if (hoursNode) hoursNode.textContent = String(hours).padStart(2, '0');
    if (minutesNode) minutesNode.textContent = String(minutes).padStart(2, '0');
    if (secondsNode) secondsNode.textContent = String(seconds).padStart(2, '0');
  };
  updateCountdown();
  window.setInterval(updateCountdown, 1000);
}

// Footer shortcut
const topButton = document.querySelector('[data-scroll-top]');
topButton?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// Respect reduced-motion preferences; otherwise reveal sections as they enter view.
const revealItems = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver((entries, activeObserver) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        activeObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  revealItems.forEach((item) => observer.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add('is-visible'));
}
