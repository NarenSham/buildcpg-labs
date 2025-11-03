// Mermaid initialization for MkDocs Material
// Save this file as: docs/javascripts/mermaid-init.js

document$.subscribe(function() {
  // Initialize mermaid with custom config
  mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    themeVariables: {
      primaryColor: '#3b82f6',
      primaryTextColor: '#1e40af',
      primaryBorderColor: '#2563eb',
      lineColor: '#64748b',
      secondaryColor: '#f59e0b',
      tertiaryColor: '#10b981',
      background: '#ffffff',
      mainBkg: '#f0f9ff',
      secondBkg: '#fef3c7',
      tertiaryBkg: '#dcfce7',
      noteBkgColor: '#e0e7ff',
      noteTextColor: '#1e40af',
      noteBorderColor: '#6366f1'
    },
    flowchart: {
      useMaxWidth: true,
      htmlLabels: true,
      curve: 'basis',
      padding: 15,
      nodeSpacing: 50,
      rankSpacing: 50
    },
    sequence: {
      diagramMarginX: 50,
      diagramMarginY: 10,
      actorMargin: 50,
      width: 150,
      height: 65,
      boxMargin: 10,
      boxTextMargin: 5,
      noteMargin: 10,
      messageMargin: 35,
      mirrorActors: true,
      useMaxWidth: true
    },
    gantt: {
      titleTopMargin: 25,
      barHeight: 20,
      barGap: 4,
      topPadding: 50,
      leftPadding: 75,
      gridLineStartPadding: 35,
      fontSize: 11,
      numberSectionStyles: 4,
      axisFormat: '%Y-%m-%d'
    },
    journey: {
      diagramMarginX: 50,
      diagramMarginY: 10,
      actorMargin: 50,
      width: 150,
      height: 65,
      boxMargin: 10,
      boxTextMargin: 5
    },
    er: {
      diagramPadding: 20,
      layoutDirection: 'TB',
      minEntityWidth: 100,
      minEntityHeight: 75,
      entityPadding: 15,
      stroke: 'gray',
      fill: 'honeydew',
      fontSize: 12,
      useMaxWidth: true
    },
    pie: {
      useMaxWidth: true
    },
    gitGraph: {
      diagramPadding: 8,
      nodeLabel: {
        width: 75,
        height: 100,
        x: -25,
        y: 0
      }
    }
  });

  // Re-render on page load
  mermaid.contentLoaded();
});

// Support for dark mode theme switching
var observer = new MutationObserver(function(mutations) {
  mutations.forEach(function(mutation) {
    if (mutation.attributeName === 'data-md-color-scheme') {
      var scheme = document.querySelector('[data-md-color-scheme]').getAttribute('data-md-color-scheme');
      var theme = scheme === 'slate' ? 'dark' : 'default';
      
      // Update mermaid theme
      mermaid.initialize({
        theme: theme
      });
      
      // Re-render all diagrams
      location.reload();
    }
  });
});

// Observe theme changes
var config = { attributes: true };
var targetNode = document.querySelector('[data-md-color-scheme]');
if (targetNode) {
  observer.observe(targetNode, config);
}