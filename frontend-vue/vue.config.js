const path = require('path');
module.exports = {
    pluginOptions: {
        i18n: {
            locale: 'en',
            fallbackLocale: 'en',
            localeDir: 'locales',
            enableInSFC: false
        }
    },
    chainWebpack: config => {
        // Remove prefetch plugin and that's it!
        config.plugins.delete('prefetch');
    },
    configureWebpack: {
        resolve: {
            alias: {
                '@themeConfig': path.resolve(__dirname, 'theme.config.js'),                
            }
        }
    },
    publicPath: '/',
    outputDir: 'dist',
    assetsDir: 'static',
    // css: {
    //   loaderOptions: {
    //     scss: {
    //       prependData: `
    //         @import "@/styles/variables.scss";
    //       `
    //     }
    //   }
    // },
    devServer: {
      proxy: {
        '^/api': {
          target: `http://localhost:8082`,
          changeOrigin: true
        }
      }
    },
};
