package jep;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * <pre>
 * NamingConventionClassEnquirer.java - A simple enquirer to see
 * if the package/class to be imported in a Python interpreter should
 * be considered as a Java package/class.
 * 
 * This class is useful for the following scenarios:
 * <ul>
 * <li>You don't want the overhead of initializing ClassList.getInstance()</li>
 * <li>You don't want all the classes in a package automatically imported</li>
 * <li>You don't have python modules that resemble java package names</li>
 * </ul>
 * 
 * 
 * Copyright (c) 2015 JEP AUTHORS.
 * 
 * This file is licenced under the the zlib/libpng License.
 * 
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any
 * damages arising from the use of this software.
 * 
 * Permission is granted to anyone to use this software for any
 * purpose, including commercial applications, and to alter it and
 * redistribute it freely, subject to the following restrictions:
 * 
 *     1. The origin of this software must not be misrepresented; you
 *     must not claim that you wrote the original software. If you use
 *     this software in a product, an acknowledgment in the product
 *     documentation would be appreciated but is not required.
 * 
 *     2. Altered source versions must be plainly marked as such, and
 *     must not be misrepresented as being the original software.
 * 
 *     3. This notice may not be removed or altered from any source
 *     distribution.
 * 
 * Created: Thurs Apr 02 2015
 * 
 * </pre>
 * 
 * @author [ndjensen at gmail.com] Nate Jensen
 * @version $Id$
 */
public class NamingConventionClassEnquirer implements ClassEnquirer {

    protected static final List<String> TOP_LEVEL = Arrays.asList("java",
            "javax", "com", "gov", "org", "edu", "mil", "net");

    protected Set<String> javaNames;

    /**
     * Convenience constructor. Includes defaults but not country codes.
     */
    public NamingConventionClassEnquirer() {
        this(true);
    }

    /**
     * Constructor
     * 
     * @param includeDefaults
     *            whether or not typical package names such as java, javax, com,
     *            gov should be considered as a java package.
     */
    public NamingConventionClassEnquirer(boolean includeDefaults) {
        this(includeDefaults, false);
    }

    /**
     * Constructor
     * 
     * @param includeDefaults
     *            whether or not typical package names such as java, javax, com,
     *            gov should be considered as a java package.
     * @param includeCountryCodes
     *            whether or not a name starting with a 2-letter country code
     *            such a uk, de, fr, us, ch should be considered as a Java
     *            package.
     */
    public NamingConventionClassEnquirer(boolean includeDefaults,
            boolean includeCountryCodes) {
        if (includeCountryCodes) {
            String[] codes = Locale.getISOCountries();
            javaNames = new HashSet<String>(TOP_LEVEL.size() + codes.length);
            javaNames.addAll(TOP_LEVEL);
            for (String country : codes) {
                javaNames.add(country.toLowerCase());
            }
        } else {
            javaNames = new HashSet<String>(TOP_LEVEL.size());
            javaNames.addAll(TOP_LEVEL);
        }
    }

    /**
     * Adds a top level package name to the list of names that should be
     * considered as Java packages
     * 
     * @param pkgStart
     */
    public void addTopLevelPackageName(String pkgStart) {
        javaNames.add(pkgStart);
    }

    @Override
    public boolean contains(String name) {
        if (name == null) {
            throw new IllegalArgumentException("name must not be null");
        }
        if (javaNames.contains(name)) {
            return true;
        } else {
            String[] split = name.split("\\.");
            return (split.length > 0 && javaNames.contains(split[0]));
        }
    }

    @Override
    public boolean supportsPackageImport() {
        return false;
    }

}