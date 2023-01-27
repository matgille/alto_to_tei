<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes="xs" version="2.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:alto="http://www.loc.gov/standards/alto/ns-v4#">

    <xsl:param name="sigle"/>
    <xsl:param name="input_files"/>
    <xsl:param name="output_file"/>
    <xsl:param name="MainZoneTag"/>
    <xsl:param name="MarginTextZoneTag"/>
    <xsl:param name="NumberingZoneTag"/>
    <xsl:param name="QuireMarksZoneTag"/>
    <xsl:param name="RunningTitleZoneTag"/>
    <xsl:param name="TitleZoneTag"/>
    <xsl:param name="DropCapitalZoneTag"/>
    <xsl:param name="HeadingLine_rubricTag"/>

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
                            <xsl:element name="p" namespace="http://www.tei-c.org/ns/1.0">Publication
                                information</xsl:element>
                        </xsl:element>
                        <xsl:element name="sourceDesc" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="p" namespace="http://www.tei-c.org/ns/1.0">Information
                                about the source</xsl:element>
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
                <xsl:element name="facsimile" namespace="http://www.tei-c.org/ns/1.0"/>
                <xsl:element name="text" namespace="http://www.tei-c.org/ns/1.0">
                    <xsl:element name="body" namespace="http://www.tei-c.org/ns/1.0">
                        <xsl:element name="div" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="p" namespace="http://www.tei-c.org/ns/1.0">
                                <xsl:for-each select="collection(concat($input_files, '?select=*.xml'))">
                                    <!--Change expression here to adapt to filenames-->
                                    <xsl:sort select="substring-after(substring-before(base-uri(), '.xml'), 'in/')"
                                        data-type="number"/>
                                    <xsl:message select="substring-after(substring-before(base-uri(), '.xml'), 'in/')"/>
                                    <xsl:variable name="folio">
                                        <xsl:value-of
                                            select="substring-after(substring-before(base-uri(), '.xml'), 'in/')"
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

    <xsl:template match="alto:PrintSpace">
        <!--Depuis eScriptorium l'export ALTO pose problème du point de vue de l'ordre des colonnes: 
        https://gitlab.com/scripta/escriptorium/-/issues/373-->
        <!--On va donc aller rétablir l'ordre en prenant la position du début de chaque zone de texte (point supérieur gauche)-->
        <!--Merci à Simon Gabay pour cette suggestion-->
        <xsl:apply-templates select="descendant::alto:TextBlock">
            <xsl:sort select="@HPOS" data-type="number"/>
        </xsl:apply-templates>

    </xsl:template>



    <xsl:template match="alto:tags">
        <!--Ici on peut se servir de la typologie pour créer une typologie dans le tei:teiHeader-->
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = $MainZoneTag]">
        <xsl:variable name="left_hor_pos">
            <xsl:value-of select="@HPOS"/>
        </xsl:variable>
        <!--On remet en place les tei:cb-->
        <xsl:if test="parent::node()/alto:TextBlock[@TAGREFS = $MainZoneTag][@HPOS > $left_hor_pos]">
            <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
                <xsl:attribute name="break">?</xsl:attribute>
            </xsl:element>
        </xsl:if>
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = $QuireMarksZoneTag]">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">reclame</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextBlock[@TAGREFS = $MarginTextZoneTag]">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">ajout</xsl:attribute>
            <xsl:attribute name="place">?</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>



    <!--<xsl:template match="alto:TextBlock[@TAGREFS = 'LT6']">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">glose</xsl:attribute>
            <xsl:attribute name="place">?</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>-->



    <!--<xsl:template match="alto:TextBlock[@TAGREFS = 'BT28']">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">margin</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>-->

    <xsl:template match="alto:TextBlock[@TAGREFS = $DropCapitalZoneTag]">
        <xsl:element name="graphic" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">lettrine</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = $RunningTitleZoneTag]">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">titre_courant</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextBlock[@TAGREFS = $NumberingZoneTag]">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">numerotation</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <xsl:template match="alto:TextBlock[not(@TAGREFS)]">
        <xsl:element name="ab" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">untyped</xsl:attribute>
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
