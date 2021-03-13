<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:tei="http://www.tei-c.org/ns/1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs" version="2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:alto="http://www.loc.gov/standards/alto/ns-v4#">

    <xsl:param name="sigle"/>
    <xsl:param name="input_files"/>
    <xsl:param name="output_file"/>

    <xsl:strip-space elements="*"/>
    <xsl:output method="xml"/>

    <xsl:template match="/">
        <xsl:result-document href="{$output_file}">
            <xsl:element name="TEI" namespace="http://www.tei-c.org/ns/1.0">
                <xsl:attribute name="xml:id">Mad_A</xsl:attribute>
                <xsl:element name="teiHeader" namespace="http://www.tei-c.org/ns/1.0">
                    <xsl:element name="fileDesc" namespace="http://www.tei-c.org/ns/1.0">
                        <xsl:element name="titleStmt" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="title" namespace="http://www.tei-c.org/ns/1.0">
                                <xsl:value-of select="$sigle"/>
                            </xsl:element>
                        </xsl:element>
                        <xsl:element name="publicationStmt" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="p" namespace="http://www.tei-c.org/ns/1.0"
                                >Publication information</xsl:element>
                        </xsl:element>
                        <xsl:element name="sourceDesc" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="p" namespace="http://www.tei-c.org/ns/1.0"
                                >Information about the source</xsl:element>
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
                <xsl:element name="facsimile" namespace="http://www.tei-c.org/ns/1.0"/>
                <xsl:element name="text" namespace="http://www.tei-c.org/ns/1.0">
                    <xsl:element name="body" namespace="http://www.tei-c.org/ns/1.0">
                        <xsl:element name="div" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="p" namespace="http://www.tei-c.org/ns/1.0">
                                <xsl:for-each
                                    select="collection(concat($input_files, '?select=*.xml'))">
                                    <xsl:sort select="base-uri()"/>
                                    <xsl:variable name="folio">
                                        <xsl:value-of
                                            select="substring-before(substring-after(substring-after(base-uri(), '/'), '-'), '.xml')"
                                        />
                                    </xsl:variable>
                                    <xsl:element name="pb" namespace="http://www.tei-c.org/ns/1.0">
                                        <xsl:attribute name="n">
                                            <xsl:value-of select="$folio"/>
                                        </xsl:attribute>
                                        <xsl:attribute name="facs">
                                            <xsl:value-of
                                                select="concat($input_files, '/', descendant::alto:Description/alto:sourceImageInformation/alto:fileName)"
                                            />
                                        </xsl:attribute>
                                    </xsl:element>
                                    <xsl:apply-templates select="descendant::alto:alto"/>
                                </xsl:for-each>
                            </xsl:element>
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
            </xsl:element>
        </xsl:result-document>
    </xsl:template>

    <xsl:template match="alto:Description"/>

    <xsl:template match="alto:alto">
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="alto:tags">
        <!--Ici on peut se servir de la typologie pour créer une typologie dans le tei:teiHeader-->
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = 'BT2']">
        <xsl:if test="preceding::alto:TextBlock[@TAGREFS = 'BT2']">
            <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
                <xsl:attribute name="break">?</xsl:attribute>
            </xsl:element>
        </xsl:if>
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = 'BT9']">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">reclame</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextBlock[@TAGREFS = 'LT3']">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">ajout</xsl:attribute>
            <xsl:attribute name="place">?</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextBlock[@TAGREFS = 'LT6']">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">glose</xsl:attribute>
            <xsl:attribute name="place">?</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextBlock[@TAGREFS = 'BT3']">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">commentaire</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = 'BT4']">
        <xsl:element name="graphic" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">lettrine</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = 'BT7']">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">titre_courant</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextBlock[@TAGREFS = 'BT8']">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">foliation</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextLine">
        <xsl:element name="lb" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="break">?</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
        <xsl:value-of select="replace(alto:String/@CONTENT, '\s$', '')"/>
    </xsl:template>

</xsl:stylesheet>
