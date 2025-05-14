// DEHA AI - Interactive Landing Page Script
document.addEventListener('DOMContentLoaded', function() {
    console.log("DEHA AI script loaded.");
    
    // Mobile Navigation
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Toggle mobile menu
    if (hamburger) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
    }
    
    // Close mobile menu when clicking a link
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });
    
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Active navigation based on scroll position
    const sections = document.querySelectorAll('section');
    
    function setActiveLink() {
        let index = sections.length;
        
        while(--index && window.scrollY + 100 < sections[index].offsetTop) {}
        
        navLinks.forEach(link => link.classList.remove('active'));
        
        if (navLinks[index]) {
            navLinks[index].classList.add('active');
        }
    }
    
    window.addEventListener('scroll', setActiveLink);
    
    // Parallax effect on hero section
    const hero = document.querySelector('.hero');
    const title = document.querySelector('.hero-title');
    const shapes = document.querySelectorAll('.shape');
    
    if (hero && shapes.length > 0) {
        hero.addEventListener('mousemove', function(e) {
            const x = e.clientX / window.innerWidth;
            const y = e.clientY / window.innerHeight;
            
            // Move title slightly
            if (title) {
                title.style.transform = `translate(${x * 15}px, ${y * 15}px)`;
            }
            
            // Move shapes in opposite directions for depth effect
            shapes.forEach((shape, index) => {
                const factor = index % 2 === 0 ? -1 : 1;
                shape.style.transform = `translate(${x * 30 * factor}px, ${y * 30 * factor}px)`;
            });
        });
        
        // Reset positions when mouse leaves
        hero.addEventListener('mouseleave', function() {
            if (title) {
                title.style.transform = 'translate(0, 0)';
            }
            shapes.forEach(shape => {
                shape.style.transform = 'translate(0, 0)';
            });
        });
    }
    
    // Form submission
    const form = document.querySelector('.contact-form form');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            // No need to prevent default since we want to actually submit to the external form
            console.log('Redirecting to Google Form');
            // Form will redirect to action URL
        });
    }
    
    // Add animation on scroll
    const animatedElements = document.querySelectorAll('.card, .feature-card, .business-card, .team-member');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, {
        threshold: 0.1
    });
    
    animatedElements.forEach(el => {
        observer.observe(el);
        el.classList.add('fade-in-element'); // Add class to enable CSS animation
    });
}); 