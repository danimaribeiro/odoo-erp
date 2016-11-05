/*
Copyright (c) 2008-2012 NaN Projectes de Programari Lliure, S.L.
                        http://www.NaN-tic.com

WARNING: This program as such is intended to be used by professional
programmers who take the whole responsability of assessing all potential
consequences resulting from its eventual inadequacies and bugs
End users who are looking for a ready-to-use solution with commercial
garantees and support are strongly adviced to contract a Free Software
Service Company

This program is Free Software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
*/
package com.nantic.jasperreports;

import java.io.File;
import java.io.InputStream;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.DriverManager;
import java.util.Hashtable;
import java.util.Locale;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

// Exporters
import net.sf.jasperreports.engine.JRAbstractExporter;
import net.sf.jasperreports.engine.JREmptyDataSource;
import net.sf.jasperreports.engine.JRExporterParameter;
import net.sf.jasperreports.engine.JRParameter;
import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JasperFillManager;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.data.JRXmlDataSource;
import net.sf.jasperreports.engine.export.JRCsvExporter;
import net.sf.jasperreports.engine.export.JRHtmlExporter;
import net.sf.jasperreports.engine.export.JRHtmlExporterParameter;
import net.sf.jasperreports.engine.export.JRPdfExporter;
import net.sf.jasperreports.engine.export.JRRtfExporter;
import net.sf.jasperreports.engine.export.JRTextExporter;
import net.sf.jasperreports.engine.export.JRTextExporterParameter;
import net.sf.jasperreports.engine.export.JRXlsExporter;
import net.sf.jasperreports.engine.export.oasis.JROdsExporter;
import net.sf.jasperreports.engine.export.oasis.JROdtExporter;
import net.sf.jasperreports.engine.util.JRLoader;

import org.apache.xmlrpc.server.PropertyHandlerMapping;
//import org.apache.xml.security.utils.Base64;
import org.apache.xmlrpc.server.XmlRpcServer;
import org.apache.xmlrpc.webserver.WebServer;
//import org.apache.xmlrpc.webserver.*;



public class JasperServer {
    /* Compiles the given .jrxml (inputFile) */
    public Boolean compile( String jrxmlPath ) throws java.lang.Exception {
        File jrxmlFile;
        File jasperFile;

        System.setProperty("jasper.reports.compiler.class", "com.nantic.jasperreports.I18nGroovyCompiler");

        jrxmlFile = new File( jrxmlPath );
        jasperFile = new File( jasperPath( jrxmlPath ) );
        if ( (! jasperFile.exists()) || (jrxmlFile.lastModified() > jasperFile.lastModified()) ) {
            System.out.println( "JasperServer: Compiling " + jrxmlPath ) ;
            JasperCompileManager.compileReportToFile( jrxmlPath, jasperPath( jrxmlPath ) );
            System.out.println( "JasperServer: Compiled.");
        }
        return true;
    }

    /* Returns path where bundle files are expected to be */
    public String bundlePath( String jrxmlPath ) {
        int index;
        index = jrxmlPath.lastIndexOf('.');
        if ( index != -1 )
            return jrxmlPath.substring( 0, index );
        else
            return jrxmlPath;
    }

    /* Returns the path to the .jasper file for the given .jrxml */
    public String jasperPath( String jrxmlPath ) {
        return bundlePath( jrxmlPath ) + ".jasper";
    }

    public int execute( Hashtable connectionParameters, String jrxmlPath, String outputPath, Hashtable parameters) throws java.lang.Exception {
         try {
            return privateExecute( connectionParameters, jrxmlPath, outputPath, parameters );
         } catch (Exception exception) {
            //exception.printStackTrace();
             throw exception;
         }
    }

    public int privateExecute( Hashtable connectionParameters, String jrxmlPath, String outputPath, Hashtable parameters) throws java.lang.Exception {


        JasperReport report = null;
        byte[] result = null;
        JasperPrint jasperPrint = null;
        InputStream in = null;
        int index;
        try{
        // Ensure report is compiled
        //compile( jrxmlPath );

        report = (JasperReport) JRLoader.loadObjectFromFile( jasperPath( jrxmlPath ) );

        // Add SUBREPORT_DIR parameter
        index = jrxmlPath.lastIndexOf('/');
        if ( index != -1 ){
        	String reportDir = jrxmlPath.substring( 0, index+1 );
            parameters.put( "SUBREPORT_DIR", reportDir );

	        Map<String, Object> props = new ReportPropertiesReader().readProperties(reportDir);
			Set<Entry<String, Object>> entries = props.entrySet();
			for (Entry<String, Object> entry : entries) {
				parameters.put( entry.getKey(), entry.getValue() );
			}
        }

        Set<Entry<Object, Object>> entries = parameters.entrySet();
        Integer ids_plain = null;
        for (Entry<Object, Object> entry : entries) {
			System.out.println(entry.getKey() + " -> " + entry.getValue());
			if(((String)entry.getKey()).equalsIgnoreCase("IDS")){
				ids_plain = treatIds(entry.getValue());
				break;
			}
		}
        if(ids_plain !=null){
        	parameters.put("IDS_PLAIN", ids_plain);
        }



        // Declare it outside the parameters loop because we'll use it when we will create the data source.
        Translator translator = null;

        // Fill in report parameters
        JRParameter[] reportParameters = report.getParameters();
        for( int j=0; j < reportParameters.length; j++ ){
            JRParameter jparam = reportParameters[j];
            if ( jparam.getValueClassName().equals( "java.util.Locale" ) ) {
                // REPORT_LOCALE
                if ( ! parameters.containsKey( jparam.getName() ) )
                    continue;
                String[] locales = ((String)parameters.get( jparam.getName() )).split( "_" );

                Locale locale;
                if ( locales.length == 1 )
                    locale = new Locale( locales[0] );
                else
                    locale = new Locale( locales[0], locales[1] );

                parameters.put( jparam.getName(), locale );

                // Initialize translation system
                // SQL reports will need to declare the TRANSLATOR paramter for translations to work.
                // CSV/XML based ones will not need that because we will integrate the translator
                // with the CsvMultiLanguageDataSource.
                translator = new Translator( bundlePath(jrxmlPath), locale );
                parameters.put( "TRANSLATOR", translator );

            } else if( jparam.getValueClassName().equals( "java.lang.BigDecimal" )){
                Object param = parameters.get( jparam.getName());
                parameters.put( jparam.getName(), new BigDecimal( (Double) parameters.get(jparam.getName() ) ) );
            }
        }
        parameters.put(JRParameter.REPORT_LOCALE, new Locale("pt","BR"));

        if ( connectionParameters.containsKey("subreports") ) {
            Object[] subreports = (Object[]) connectionParameters.get("subreports");
            for (int i = 0; i < subreports.length; i++ ) {
                Map m = (Map)subreports[i];

                // Ensure subreport is compiled
                String jrxmlFile = (String)m.get("jrxmlFile");
                if ( ! jrxmlFile.equals( "DATASET" ) )
                    compile( (String)m.get("jrxmlFile") );

                // Create DataSource for subreport
                CsvMultiLanguageDataSource dataSource = new CsvMultiLanguageDataSource( (String)m.get("dataFile"), "utf-8", translator );
                System.out.println( "JasperServer: Adding parameter '" + ( (String)m.get("parameter") ) + "' with datasource '" + ( (String)m.get("dataFile") ) + "'" );

                parameters.put( m.get("parameter"), dataSource );
            }
        }

        System.out.println( "JasperServer: Filling report..." );
        System.out.println("Print params:");
        this.printParams(parameters);

        // Fill in report
        String language;
        if ( report.getQuery() == null )
            language = "";
        else
            language = report.getQuery().getLanguage();

        System.out.println("Language = " + language);
        if( language.equalsIgnoreCase( "XPATH")  ){
            // If available, use a CSV file because it's faster to process.
            // Otherwise we'll use an XML file.
            if ( connectionParameters.containsKey("csv") ) {
                CsvMultiLanguageDataSource dataSource = new CsvMultiLanguageDataSource( (String)connectionParameters.get("csv"), "utf-8", translator );
                jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
            } else {
                JRXmlDataSource dataSource = new JRXmlDataSource( (String)connectionParameters.get("xml"), "/data/record" );
                dataSource.setDatePattern( "yyyy-MM-dd HH:mm:ss" );
                dataSource.setNumberPattern( "#######0.##" );
                dataSource.setLocale( Locale.ENGLISH );
                jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
            }
        } else if( language.equalsIgnoreCase( "SQL")  ) {
            System.out.println("Language = " + language);
            System.out.println( "JasperServer: Abrindo conexao com o BD" );
            System.out.println("ConnectionParameters = " + connectionParameters);
            Connection connection = getConnection( connectionParameters );
            this.printParams(parameters);
            jasperPrint = JasperFillManager.fillReport( report, parameters, connection );
            connection.close();
            System.out.println( "JasperServer: Fechou conexao com o BD" );
        } else {
            JREmptyDataSource dataSource = new JREmptyDataSource();
            jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
        }

        // Create output file
        File outputFile = new File( outputPath );
        JRAbstractExporter exporter;

        String output;
        if ( connectionParameters.containsKey( "output" ) )
            output = (String)connectionParameters.get("output");
        else
            output = "pdf";

        System.out.println( "JasperServer: Exporting..." );
        if ( output.equalsIgnoreCase( "html" ) ) {
            exporter = new JRHtmlExporter();
            exporter.setParameter(JRHtmlExporterParameter.IS_USING_IMAGES_TO_ALIGN, Boolean.FALSE);
            exporter.setParameter(JRHtmlExporterParameter.HTML_HEADER, "");
            exporter.setParameter(JRHtmlExporterParameter.BETWEEN_PAGES_HTML, "");
            exporter.setParameter(JRHtmlExporterParameter.IS_REMOVE_EMPTY_SPACE_BETWEEN_ROWS, Boolean.TRUE);
            exporter.setParameter(JRHtmlExporterParameter.HTML_FOOTER, "");
        } else if ( output.equalsIgnoreCase( "csv" ) ) {
            exporter = new JRCsvExporter();
        } else if ( output.equalsIgnoreCase( "xls" ) ) {
            exporter = new JRXlsExporter();
        } else if ( output.equalsIgnoreCase( "rtf" ) ) {
            exporter = new JRRtfExporter();
        } else if ( output.equalsIgnoreCase( "odt" ) ) {
            exporter = new JROdtExporter();
        } else if ( output.equalsIgnoreCase( "ods" ) ) {
            exporter = new JROdsExporter();
        } else if ( output.equalsIgnoreCase( "txt" ) ) {
            exporter = new JRTextExporter();
            exporter.setParameter(JRTextExporterParameter.PAGE_WIDTH, new Integer(80));
            exporter.setParameter(JRTextExporterParameter.PAGE_HEIGHT, new Integer(150));
        } else {
            exporter = new JRPdfExporter();
        }
        exporter.setParameter(JRExporterParameter.JASPER_PRINT, jasperPrint);
        exporter.setParameter(JRExporterParameter.OUTPUT_FILE, outputFile);
        exporter.exportReport();
        System.out.println( "JasperServer: Exported." );
    }catch(Exception e){
        e.printStackTrace();
        throw e;

    }
    return jasperPrint.getPages().size();
    }

    private void printParams(Hashtable parameters) {
		if (parameters!=null){
			System.out.println("Parâmetros enviados ao jasper:\n");
			Set entries = parameters.entrySet();
			for (Object object : entries) {
				System.out.println("  - "+object+ " = " + parameters.get(object));
			}
			System.out.println("Fim dos parâmetros enviados");
			System.out.println("-- xx --");
		}

	}

	private Integer treatIds(Object param) {
    	Object[] ids = (Object[])param;
    	Integer item = null;
    	for (Object object : ids) {
			item = (Integer)object;
		}
    	System.out.println("Criando relatório para id " + item);
		return item;
	}


	public static Connection getConnection( Hashtable datasource ) throws java.lang.ClassNotFoundException, java.sql.SQLException {
        Connection connection;
        Class.forName("org.postgresql.Driver");
        connection = DriverManager.getConnection( (String)datasource.get("dsn"), (String)datasource.get("user"),
        (String)datasource.get("password") );
        connection.setAutoCommit(true);
        return connection;
    }

    public static void main (String [] args) {
    	WebServer server = null;
        try {
            int port = 8090;
            if ( args.length > 0 ) {
                port = java.lang.Integer.parseInt( args[0] );
            }
            java.net.InetAddress localhost = java.net.Inet4Address.getByName("localhost");
            System.out.println("JasperServer: Attempting to start XML-RPC Server at " + localhost.toString() + ":" + port + "...");
            server = new WebServer( port, localhost );
            XmlRpcServer xmlRpcServer = server.getXmlRpcServer();

            PropertyHandlerMapping phm = new PropertyHandlerMapping();
            phm.addHandler("Report", JasperServer.class);
            xmlRpcServer.setHandlerMapping(phm);

            server.start();
            System.out.println("JasperServer: Started successfully.");
            System.out.println("JasperServer: Accepting requests. (Halt program to stop.)");
        } catch (Exception exception) {
            System.err.println("Jasper Server: " + exception);
            if(server!=null){
        		server.shutdown();
        	}
        }
    }
}
