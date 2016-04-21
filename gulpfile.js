// Include gulp
var gulp = require('gulp');
// Include plugins
var sass = require('gulp-sass');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var rename = require('gulp-rename');
var browserSync = require('browser-sync').create();
var reload = browserSync.reload;
var jshint = require('gulp-jshint');
var runSequence = require('run-sequence');

var templateCache = require('gulp-angular-templatecache');
var minfyHtml = require('gulp-minify-html');
var fs = require('fs');
var plumber = require('gulp-plumber');
var insert = require('gulp-insert');
// Define base folders
var _root = __dirname + '/';
var _app = _root + 'app/'
var _source = _app + 'src/';
var _path = {
  bower: _app + '/bower_components',
  js: _source + 'js/', //TODO adjust these when we figure out our file structure
  css: _source + 'styles/css/',
  sass: _source +'styles/sass',
  dist: _app + 'dist/', //TODO add local/prod/stage/dev ect...
};
var   jsToCompile = [
     _source + '/app.js',
     _source + '/controllers/*.js',
     _source + '/views/templates.js'
  ];

//TODO can use globs to help easier determine what files to compile when building dist

gulp.task('js-lint', function() {
  gulp.src(jsToCompile)
  .pipe(jshint())
  .pipe(jshint.reporter('default'));

  gulp.watch([jsToCompile], reload);
});

// Spin up a server
gulp.task('server', function() {

  browserSync.init({
    port: 8080,
    server: {
      baseDir: _source //this is where the server will run index.html from
    }
  })
});

gulp.task('build', function(cb) {
  runSequence('js-lint', cb);
});

 // Watch for changes in files
 gulp.task('watch', function() {
    // Watch .js files
    gulp.watch([jsToCompile], ['js-lint']);
   });
 // Default Task
gulp.task('default', ['watch', 'build', 'server']);
