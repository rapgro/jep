from __future__ import print_function

from distutils.cmd import Command
from distutils.spawn import spawn
import shutil
import os
import fnmatch
import traceback
import sys
from commands.util import configure_error, is_osx, shell, CommandFailed, warning

_java_home = None
# MAC_JAVA_HOME is for the Apple JDK and is consistent in its install directory.
# For better or for worse, Apple stopped supporting a JDK after Java 1.6.
MAC_JAVA_HOME = '/System/Library/Frameworks/JavaVM.framework'


def get_java_home():
    global _java_home
    if _java_home is not None:
        return _java_home

    if is_osx():
        # newer macs have an executable to help us
        try:
            result = shell('/usr/libexec/java_home')
            _java_home = result.stdout
            return _java_home
        except CommandFailed:
            traceback.print_exc()
            if not os.path.exists(MAC_JAVA_HOME):
                configure_error('No JAVA_HOME')

        # Apple's JAVA_HOME is predictable, just use that if we can
        # though it doesn't work for Oracle's JDK
        if os.path.exists(MAC_JAVA_HOME):
            _java_home = MAC_JAVA_HOME
            return _java_home

    env_home = os.environ.get('JAVA_HOME')
    if env_home and os.path.exists(env_home):
        _java_home = env_home
        return env_home

    configure_error("Please set JAVA_HOME to a path containing the JDK.")


def is_apple_jdk():
    """
    Checks if the JDK installed is Apple's JDK.  Apple's JDK layout is
    different than others, while Oracle's JDK layout consistently has
    a bin, include, and lib dir.
    """
    return get_java_home() == MAC_JAVA_HOME


def get_java_include():
    """
    Locate the Java include folders for compiling JNI applications.
    """
    inc_name = 'include'
    if is_apple_jdk():
        inc_name = 'Headers'
    inc = os.path.join(get_java_home(), inc_name)
    if not os.path.exists(inc):
        configure_error("Include folder should be at '{0}' but doesn't exist. " \
                        "Please check you've installed the JDK properly.".format(inc))
    jni = os.path.join(inc, "jni.h")
    if not os.path.exists(jni):
        configure_error("jni.h should be in '{0}' but doesn't exist. " \
                        "Please check you've installed the JDK properly.".format(jni))

    paths = [inc]
    
    # Include platform specific headers if found
    include_linux = os.path.join(inc, 'linux')
    if os.path.exists(include_linux):
        paths.append(include_linux)

    include_darwin = os.path.join(inc, 'darwin')
    if os.path.exists(include_darwin):
        paths.append(include_darwin)
    return paths


def get_java_lib():
    lib_name = 'lib'
    if is_apple_jdk():
        lib_name = 'Libraries'
    lib = os.path.join(get_java_home(), lib_name)
    if not os.path.exists(lib):
        configure_error("Lib folder should be at '{0}' but doesn't exist. " \
                        "Please check you've installed the JDK properly.".format(lib))
    return lib


def get_java_libraries():
    if not is_osx():
        return ['jvm']
    return []


def get_java_lib_folders():
    if not is_osx():
        jre = os.path.join(get_java_home(), 'jre', 'lib')
        folders = []
        for root, dirnames, filenames in os.walk(jre):
            for filename in fnmatch.filter(filenames, '*jvm.so'):
                folders.append(os.path.join(root, os.path.dirname(filename)))

        return list(set(folders))
    return []


def get_java_linker_args():
    if is_apple_jdk():
        return ['-framework JavaVM']
    return []


class setup_java(Command):
    """
    Output some useful information about the java environment
    This is useful when people report errors
    """

    user_options = []

    def initialize_options(self):
        pass

    def run(self):
        warning('Using JAVA_HOME:', get_java_home())

        if is_osx():
            target = os.environ.get('MACOSX_DEPLOYMENT_TARGET')

            if target:
                warning('INFO: the MACOSX_DEPLOYMENT_TARGET environment variable is set:', target)

                result = shell('sw_vers -productVersion')
                if target.split('.')[:2] != result.stdout.split('.')[:2]:
                    warning('This target appears to be incorrect for the system version:', result.stdout)

    def finalize_options(self):
        pass


class build_java(Command):
    outdir = None

    user_options = [
        ('javac=', None, 'use javac (default: {0}/bin/javac)'.format(get_java_home())),
    ]

    def initialize_options(self):
        build_java.outdir = os.path.join('build', 'java')
        if not os.path.exists(build_java.outdir):
            os.makedirs(build_java.outdir)

        self.java_files = []
        if is_apple_jdk():
            self.javac = os.path.join(get_java_home(), 'Commands', 'javac')
        else:
            self.javac = os.path.join(get_java_home(), 'bin', 'javac')

    def finalize_options(self):
        self.java_files = self.distribution.java_files

    def build(self, *jclasses):
        spawn([self.javac, '-deprecation', '-d', build_java.outdir, '-classpath', 'src/'] + list(*jclasses))

    def run(self):
        self.build(self.java_files)


class build_jar(Command):
    outdir = None

    user_options = [
        ('jar=', None, 'use javac (default: {0}/bin/jar)'.format(get_java_home())),
    ]

    def initialize_options(self):
        build_jar.outdir = os.path.join('build', 'java')
        if not os.path.exists(build_jar.outdir):
            os.makedirs(build_java.outdir)

        self.java_files = []
        self.extra_jar_files = []
        if is_apple_jdk():
            self.jar = os.path.join(get_java_home(), 'Commands', 'jar')
        else:
            self.jar = os.path.join(get_java_home(), 'bin', 'jar')

    def finalize_options(self):
        self.extra_jar_files = self.distribution.extra_jar_files

    def build(self):
        for src in self.extra_jar_files:
            dest = os.path.join(*['build/java'] + src.split(os.sep)[1:])
            dest_dir = os.path.dirname(dest)
            print('copying {0} to {1}'.format(src, dest))
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copyfile(src, dest)

        spawn([self.jar, '-cfe', 'build/java/jep.jar', 'jep.Run', '-C', 'build/java/', 'jep'])

    def run(self):
        self.build()


class build_javah(Command):
    outdir = None

    user_options = [
        ('javah=', None, 'use javah (default: {0}/bin/javah)'.format(get_java_home())),
    ]

    def initialize_options(self):
        build_javah.outdir = os.path.join('build', 'include')
        if not os.path.exists(build_javah.outdir):
            os.mkdir(build_javah.outdir)

        if is_apple_jdk():
            self.javah = os.path.join(get_java_home(), 'Commands', 'javah')
        else:
            self.javah = os.path.join(get_java_home(), 'bin', 'javah')
        self.javah_files = []

    def finalize_options(self):
        self.javah_files = self.distribution.javah_files or []

    def build(self, jclass, header):
        spawn([self.javah, '-classpath', build_java.outdir, '-o', os.path.join(build_javah.outdir, header), jclass])

    def run(self):
        for jclass, header in self.javah_files:
            self.build(jclass, header)
